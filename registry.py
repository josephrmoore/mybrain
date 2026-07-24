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


def find_modules_for(file_extension=None, keyword=None, folder=None, event=None):
    """
    Returns the list of registered modules whose 'claims' match any of the
    given criteria. An empty list is a normal, expected outcome — it means
    no module is registered to handle this input yet, not an error.
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
        if event and event in (claims.get("event") or []):
            matches.append(module)
            continue

    return matches
