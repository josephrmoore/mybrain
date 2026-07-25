import os
import hashlib
import shutil

import events
import file_utils


def hash_file(path, chunk_size=65536):
    """Returns a SHA-256 hex digest of the file's contents, read in chunks
    so large files don't need to be loaded into memory all at once."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(folder_path):
    """
    Recursively scans folder_path for files with identical content.
    Returns {hash: [paths]} — only groups with more than one file
    (actual duplicates), never singletons.

    Efficient by design for large folders: groups files by size first
    (cheap, no file reads), and only hashes files within a group that
    shares its size with at least one other file — files of different
    sizes can never be duplicates, so this skips hashing most files
    in a typical folder entirely.
    """
    folder_path = os.path.expanduser(folder_path)

    size_groups = {}
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.startswith("."):
                continue
            full_path = os.path.join(root, filename)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue
            size_groups.setdefault(size, []).append(full_path)

    hash_groups = {}
    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue  # unique size in the whole scan — cannot be a duplicate, skip hashing entirely
        for path in paths:
            file_hash = hash_file(path)
            hash_groups.setdefault(file_hash, []).append(path)

    return {h: paths for h, paths in hash_groups.items() if len(paths) > 1}


def _is_under(path, folder):
    path = os.path.abspath(path)
    folder = os.path.abspath(folder)
    return path == folder or path.startswith(folder + os.sep)


def choose_keeper(paths, preferred_folder=None):
    """
    Decides which of a group of duplicate paths stays in place.
    Descending priority, less entropy at each step:
    1. If exactly one copy sits inside preferred_folder, keep that one.
       If more than one does, narrow to just those and continue to the
       next tiebreaker among them rather than the whole group.
    2. Oldest by creation date (among whichever set step 1 left us with).
    3. Alphabetically first path, as a final deterministic tiebreak —
       there should never be a real tie left by this point, but ties
       must resolve to the same answer every time regardless.
    """
    candidates = paths

    if preferred_folder:
        preferred_folder = os.path.expanduser(preferred_folder)
        in_preferred = [p for p in paths if _is_under(p, preferred_folder)]
        if in_preferred:
            candidates = in_preferred

    return sorted(candidates, key=lambda p: (file_utils.get_creation_date(p), p))[0]


def review_duplicates(folder_path, review_folder, preferred_folder=None):
    """
    Finds duplicates under folder_path, keeps one copy of each group
    (per choose_keeper's priority), and moves every other copy to
    review_folder. Never deletes anything, never overwrites (collision-
    safe). Emits a 'duplicate_resolved' event per group.
    Returns a list of {"hash", "kept", "moved_to_review"}.
    """
    duplicates = find_duplicates(folder_path)
    results = []

    for file_hash, paths in duplicates.items():
        keeper = choose_keeper(paths, preferred_folder=preferred_folder)
        moved = []
        for path in paths:
            if path == keeper:
                continue
            filename = os.path.basename(path)
            dest_path = file_utils.unique_destination_path(os.path.expanduser(review_folder), filename)
            shutil.move(path, dest_path)
            moved.append(dest_path)

        result = {"hash": file_hash, "kept": keeper, "moved_to_review": moved}
        events.emit("duplicate_resolved", result)
        results.append(result)

    return results
