import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import registry
import module_loader
import config as core_config
import file_utils


class _ModuleDispatchHandler(FileSystemEventHandler):
    """Watches for new files and dispatches them to whichever registered
    module(s) claim them, via the same registry + loader path used
    everywhere else. Never crashes the watcher itself — a dispatch
    failure for one file is logged and the watcher keeps running."""

    def on_created(self, event):
        if event.is_directory:
            return
        self._dispatch(event.src_path)

    def _dispatch(self, path):
        filename = os.path.basename(path)
        if file_utils.is_hidden(filename):
            return  # ignore hidden files, same convention as organize_folder
        ext = os.path.splitext(filename)[1]
        matches = registry.find_modules_for_file(file_extension=ext)
        for module_entry in matches:
            try:
                module_loader.invoke(module_entry, path)
            except Exception as e:
                print(f"[watcher] Dispatch to '{module_entry.get('name')}' failed for {path}: {e}")


def start_watchers():
    """
    Starts a filesystem watcher for every folder any registered module
    claims (config-driven — no module-specific code here). Returns the
    list of running Observer instances; caller must keep a reference so
    they aren't garbage-collected and stopped.
    """
    cfg = core_config.load_config()
    modules = cfg.get("modules", []) or []

    watched_folders = set()
    for module in modules:
        if not isinstance(module, dict):
            continue
        claims = module.get("claims") or {}
        for folder in claims.get("folder") or []:
            watched_folders.add(os.path.expanduser(folder))

    handler = _ModuleDispatchHandler()
    observers = []
    for folder in watched_folders:
        if not os.path.isdir(folder):
            print(f"[watcher] Skipping watch folder that doesn't exist: {folder}")
            continue
        observer = Observer()
        observer.schedule(handler, folder, recursive=False)
        observer.start()
        observers.append(observer)
        print(f"[watcher] Watching: {folder}")

    return observers
