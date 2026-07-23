import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "events.log")

_subscribers = {}


def subscribe(event_name, callback):
    """Registers callback to be called whenever event_name is emitted."""
    _subscribers.setdefault(event_name, []).append(callback)


def emit(event_name, payload=None):
    """
    Fires event_name synchronously to all subscribers, in registration order.
    Always logged (to console and to events.log), regardless of whether
    anyone is subscribed. A subscriber that raises is caught and logged —
    it does not stop other subscribers from running, and never crashes
    the module that emitted the event.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    _log_event(timestamp, event_name, payload)

    for callback in _subscribers.get(event_name, []):
        try:
            callback(payload)
        except Exception as e:
            print(f"[events] Subscriber for '{event_name}' raised an error, continuing: {e}")


def _log_event(timestamp, event_name, payload):
    line = f"{timestamp} | {event_name} | {payload}"
    print(f"[events] {line}")
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")
