import os
from datetime import datetime, timezone

from paths import BASE_DIR

LOG_PATH = os.path.join(BASE_DIR, "events.log")

_subscribers = {}


def subscribe(event_name, callback):
    """Registers callback to be called whenever event_name is emitted."""
    _subscribers.setdefault(event_name, []).append(callback)


def log(module_name, message):
    """
    Console-only diagnostic/warning logging, in the '[modulename] message'
    format every module already used, hand-typed separately in each one
    (api_client, local_llm, credentials, db, registry, router, watcher,
    config, file_organizer, ableton_scanner). Pulled here since events.py
    is already the module that owns console+file logging for the event
    bus -- this is the same responsibility for ad-hoc messages instead of
    structured events.

    Deliberately console-only, matching prior behavior exactly -- does
    NOT also write to events.log. These were ephemeral prints before;
    making them persistent would be a real behavior change, not a
    refactor, and isn't part of this chunk.
    """
    print(f"[{module_name}] {message}")


def emit(event_name, payload=None):
    """
    Fires event_name synchronously to all subscribers, in registration order.
    Always attempted to be logged (to console and to events.log), regardless
    of whether anyone is subscribed. A failure to write the log does not
    prevent subscribers from running, and a subscriber that raises is caught
    and logged — neither failure mode stops the rest of this function.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    _log_event(timestamp, event_name, payload)

    for callback in _subscribers.get(event_name, []):
        try:
            callback(payload)
        except Exception as e:
            log("events", f"Subscriber for '{event_name}' raised an error, continuing: {e}")


def _log_event(timestamp, event_name, payload):
    line = f"{timestamp} | {event_name} | {payload}"
    print(f"[events] {line}")
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError as e:
        log("events", f"Couldn't write to events.log, continuing without persisting this entry: {e}")
