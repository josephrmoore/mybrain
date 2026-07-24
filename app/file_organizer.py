import os
import shutil
from datetime import datetime

import config as core_config
import events


def load_rules():
    """Pulls this module's own rules block out of the shared config file."""
    cfg = core_config.load_config()
    for module in cfg.get("modules", []) or []:
        if isinstance(module, dict) and module.get("name") == "file_organizer":
            return module.get("rules", {}) or {}
    return {}


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


def find_category(filename, categories):
    """Returns the matching category name for a file's extension, or None."""
    ext = os.path.splitext(filename)[1].lower()
    for cat in categories:
        if ext in [e.lower() for e in cat.get("extensions", [])]:
            return cat["name"]
    return None


def resolve_destination(path, rules):
    """Returns the category/date destination folder for a file, or None
    if no configured category matches its extension."""
    filename = os.path.basename(path)
    category = find_category(filename, rules.get("categories", []))
    if category is None:
        return None

    creation_date = get_creation_date(path)
    date_folder = creation_date.strftime("%Y-%m")

    base_folder = os.path.expanduser(rules["base_folder"])
    return os.path.join(base_folder, category, date_folder)


def unique_destination_path(dest_folder, filename):
    """Returns a collision-safe destination path, appending a numeric
    suffix if needed. Never overwrites an existing file."""
    os.makedirs(dest_folder, exist_ok=True)
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(dest_folder, filename)
    suffix = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dest_folder, f"{base}_{suffix}{ext}")
        suffix += 1
    return candidate


def organize_file(path, rules=None):
    """
    Organizes a single file: moves it to its category/date destination
    if a rule matches, or to needs_review if nothing matches. Never
    deletes, never overwrites. Emits a 'file_processed' event either way.
    Returns {"source", "destination", "matched"}.

    rules defaults to this module's own config entry if not given —
    this is what lets a generic loader invoke this function knowing
    nothing about file_organizer's specific configuration shape.
    """
    if rules is None:
        rules = load_rules()

    if not os.path.isfile(path):
        raise ValueError(f"Not a file: {path}")

    filename = os.path.basename(path)
    dest_folder = resolve_destination(path, rules)
    matched = dest_folder is not None

    if not matched:
        dest_folder = os.path.expanduser(rules["needs_review_folder"])

    dest_path = unique_destination_path(dest_folder, filename)
    shutil.move(path, dest_path)

    result = {"source": path, "destination": dest_path, "matched": matched}
    events.emit("file_processed", result)
    return result


def organize_folder(folder_path, rules=None):
    """
    Organizes every file directly inside folder_path (not recursive).
    Skips hidden files (dotfiles like .DS_Store) and subdirectories.
    Returns a list of per-file results from organize_file.

    rules defaults to this module's own config entry if not given.
    """
    if rules is None:
        rules = load_rules()

    folder_path = os.path.expanduser(folder_path)
    results = []
    for entry in sorted(os.listdir(folder_path)):
        if entry.startswith("."):
            continue
        full_path = os.path.join(folder_path, entry)
        if not os.path.isfile(full_path):
            continue
        results.append(organize_file(full_path, rules))
    return results
