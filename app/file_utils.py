import os
from datetime import datetime


def is_hidden(filename):
    """True for dotfiles (.DS_Store, .gitkeep, etc). The one piece of
    filtering logic every folder-scanning module needs identically —
    file_organizer, dedup_finder, watcher, and ableton_scanner each had
    their own copy of this exact check before it was pulled here."""
    return filename.startswith(".")


def get_creation_date(path):
    """Returns a datetime for the file's creation date. Falls back to
    modification time if creation time isn't tracked on this filesystem
    (this happens on Linux; macOS's APFS/HFS+ track true creation time
    via st_birthtime, which is what this is really built for)."""
    stat = os.stat(path)
    try:
        return datetime.fromtimestamp(stat.st_birthtime)
    except AttributeError:
        return datetime.fromtimestamp(stat.st_mtime)


def unique_destination_path(dest_folder, filename):
    """Returns a collision-safe destination path in dest_folder for
    filename, appending a numeric suffix if needed. Never overwrites."""
    os.makedirs(dest_folder, exist_ok=True)
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_folder, filename)
    suffix = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_folder, f"{base}_{suffix}{ext}")
        suffix += 1
    return candidate
