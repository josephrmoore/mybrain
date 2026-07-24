import importlib


def load_handler(module_entry):
    """
    Given a registry module entry with handler_type 'local' and
    handler_mechanism 'python', dynamically resolves handler
    ('module_name.function_name') into the actual callable.
    """
    handler_path = module_entry["handler"]
    module_name, func_name = handler_path.rsplit(".", 1)
    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)


def invoke(module_entry, *args, **kwargs):
    """
    Resolves and calls a module's handler function with the given args.

    Only handler_type 'local' with handler_mechanism 'python' is
    implemented right now — that's the only real module (file_organizer)
    this system has. Anything else raises NotImplementedError explicitly
    rather than silently failing or pretending to dispatch correctly.
    """
    handler_type = module_entry.get("handler_type")
    if handler_type != "local":
        raise NotImplementedError(
            f"Dispatch for handler_type '{handler_type}' isn't implemented yet "
            f"(only 'local' is supported so far)."
        )

    mechanism = module_entry.get("handler_mechanism")
    if mechanism != "python":
        raise NotImplementedError(
            f"Dispatch for handler_mechanism '{mechanism}' isn't implemented yet "
            f"(only 'python' is supported so far)."
        )

    handler_fn = load_handler(module_entry)
    return handler_fn(*args, **kwargs)
