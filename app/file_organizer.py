import os
import shutil

import config as core_config
import events
import router
import file_utils


def load_rules():
    """Pulls this module's own rules block out of the shared config file."""
    cfg = core_config.load_config()
    for module in cfg.get("modules", []) or []:
        if isinstance(module, dict) and module.get("name") == "file_organizer":
            rules = module.get("rules", {}) or {}
            validate_categories(rules.get("categories", []))
            return rules
    return {}


def find_category(filename, categories):
    """Returns the matching category name for a file's extension, or None."""
    ext = os.path.splitext(filename)[1].lower()
    for cat in categories:
        if ext in [e.lower() for e in cat.get("extensions", [])]:
            return cat["name"]
    return None


def validate_categories(categories):
    """
    Checks for the same extension listed in more than one category.
    find_category() silently picks whichever category comes first in
    the list when this happens, so this makes that risk visible instead
    of leaving it as a silent, hard-to-notice misconfiguration. Returns
    a dict of {extension: [category names it appears in]} for every
    extension that's duplicated — empty if there are no duplicates.
    """
    seen = {}
    for cat in categories:
        for ext in cat.get("extensions", []):
            ext = ext.lower()
            seen.setdefault(ext, []).append(cat.get("name", "unnamed"))

    duplicates = {ext: names for ext, names in seen.items() if len(names) > 1}
    if duplicates:
        for ext, names in duplicates.items():
            print(f"[file_organizer] WARNING: '{ext}' appears in multiple categories {names} — "
                  f"'{names[0]}' will always win, the others never will.")
    return duplicates


def build_classification_prompt(filename, category_names):
    """The prompt sent to local/API models for the fuzzy fallback. Uses
    only the filename — reading actual file contents is a separate,
    bigger decision (privacy, binary handling) not part of this pass."""
    return (
        f"Given only the filename '{filename}', which of these categories fits best: "
        f"{', '.join(category_names)}? Reply with ONLY the category name, nothing else."
    )


def organize_file(path, rules=None):
    """
    Organizes a single file. Every file goes through the same router
    escalation: deterministic extension match first, then a fuzzy
    filename-based guess (local LLM, then API) if no rule matched, then
    needs_review if nothing resolved it. Never deletes, never overwrites.
    Emits a 'file_processed' event either way.
    Returns {"source", "destination", "matched", "decided_by"}.
    """
    if rules is None:
        rules = load_rules()

    if not os.path.isfile(path):
        raise ValueError(f"Not a file: {path}")

    filename = os.path.basename(path)
    categories = rules.get("categories", [])
    category_names = [c["name"] for c in categories]

    decision = router.escalate(
        rule_fn=lambda: find_category(filename, categories),
        llm_prompt=build_classification_prompt(filename, category_names) if category_names else None,
        context=f"classify file: {filename}",
    )

    guessed = decision["result"]
    decided_by = decision["decided_by"]

    if decided_by == "local":
        category = guessed  # came straight from find_category, already trustworthy by construction
    elif decided_by in ("local_llm", "api") and guessed and guessed.strip() in category_names:
        category = guessed.strip()
    else:
        # either genuinely unresolved, or a model guessed something not in
        # our configured categories — both cases mean needs_review from here
        category = None
        decided_by = "human"

    if category is not None:
        creation_date = file_utils.get_creation_date(path)
        date_folder = creation_date.strftime("%Y-%m")
        base_folder = os.path.expanduser(rules["base_folder"])
        dest_folder = os.path.join(base_folder, category, date_folder)
        matched = True
    else:
        dest_folder = os.path.expanduser(rules["needs_review_folder"])
        matched = False

    dest_path = file_utils.unique_destination_path(dest_folder, filename)
    shutil.move(path, dest_path)

    result = {"source": path, "destination": dest_path, "matched": matched, "decided_by": decided_by}
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
        if file_utils.is_hidden(entry):
            continue
        full_path = os.path.join(folder_path, entry)
        if not os.path.isfile(full_path):
            continue
        results.append(organize_file(full_path, rules))
    return results
