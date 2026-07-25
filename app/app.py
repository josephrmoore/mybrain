from flask import Flask
import db
import config
import credentials
import watcher

app = Flask(__name__)

PORT = 5151


@app.route("/")
def index():
    return "Core Shell — Running"


if __name__ == "__main__":
    try:
        db.backup_on_launch()
        db.run_migrations()
        loaded_config = config.load_config()
        print(f"Loaded config: {loaded_config}")

        if credentials.get_anthropic_key():
            print("Anthropic API key: configured.")
        else:
            print("Anthropic API key: not set — modules will run in no-key mode until you run set_credential.py.")

        active_watchers = watcher.start_watchers()
    except Exception as e:
        print()
        print(f"FATAL: Core Shell failed to start up: {e}")
        print("Check the message above for details before trying again.")
        raise SystemExit(1)

    app.run(host="127.0.0.1", port=PORT)
