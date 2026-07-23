from flask import Flask
import db
import config
import credentials

app = Flask(__name__)

PORT = 5151


@app.route("/")
def index():
    return "Core Shell — Running"


if __name__ == "__main__":
    db.backup_on_launch()
    db.run_migrations()
    loaded_config = config.load_config()
    print(f"Loaded config: {loaded_config}")

    if credentials.get_anthropic_key():
        print("Anthropic API key: configured.")
    else:
        print("Anthropic API key: not set — modules will run in no-key mode until you run set_credential.py.")

    app.run(host="127.0.0.1", port=PORT)
