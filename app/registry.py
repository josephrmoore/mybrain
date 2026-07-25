import config


def _get_modules():
    cfg = config.load_config()
    modules = cfg.get("modules", []) or []
    valid_modules = []
    for m in modules:
        if isinstance(m, dict):
            valid_modules.append(m)
        else:
            print(f"[registry] Skipping malformed module entry (not a mapping): {m!r}")
    return valid_modules


def list_modules():
    """Returns every registered module, as defined in config.yaml."""
    return _get_modules()


def find_modules_for_file(file_extension=None, keyword=None, folder=None):
    """
    Returns the list of registered modules whose 'claims' match any of the
    given file properties (extension, keyword, or folder). An empty list
    is a normal, expected outcome — no module registered for this input yet.
    """
    matches = []
    for module in _get_modules():
        claims = module.get("claims") or {}

        if file_extension and file_extension in (claims.get("file_extension") or []):
            matches.append(module)
            continue
        if keyword and keyword in (claims.get("keyword") or []):
            matches.append(module)
            continue
        if folder and folder in (claims.get("folder") or []):
            matches.append(module)
            continue

    return matches


def find_modules_for_event(event):
    """
    Returns the list of registered modules subscribed to the given event
    name. This is a different kind of match than find_modules_for_file —
    an event is a signal from the event bus, not a property of a file.
    """
    matches = []
    for module in _get_modules():
        claims = module.get("claims") or {}
        if event in (claims.get("event") or []):
            matches.append(module)

    return matches
