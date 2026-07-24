import os
import yaml

from paths import BASE_DIR

CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

DEFAULT_CONFIG = {
    "silos": {},
    "modules": []
}

DEFAULT_CONFIG_TEMPLATE = """\
# Core Shell config
# Hand-edit this file to add silo-specific categories and settings.
# Modules read this through the shared config loader (config.py) —
# modules should never parse this file directly.

silos: {}

# Registered modules. Each entry declares what input it claims and how
# it's handled. Example (not active until you uncomment and edit it):
#
# modules:
#   - name: file_organizer
#     silo: general
#     handler_type: bash        # bash | hazel | local-llm | api
#     handler: modules/file_organizer/run.sh
#     claims:
#       file_extension: [".pdf", ".docx"]
#       keyword: ["invoice", "receipt"]
#       folder: ["~/Desktop/inbox"]
#       event: []
modules: []
"""


def load_config():
    """Returns the config as a dict. Creates a default file if missing.
    Falls back to safe in-memory defaults (without touching the file)
    if the existing file is malformed, so a typo can't crash the app."""
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)
        print(f"No config.yaml found — created a default one at {CONFIG_PATH}")
        return dict(DEFAULT_CONFIG)

    try:
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            print(f"WARNING: config.yaml did not parse as a mapping (got {type(data).__name__} instead), using safe defaults instead.")
            return dict(DEFAULT_CONFIG)
        return data
    except yaml.YAMLError as e:
        print(f"WARNING: config.yaml is malformed, using safe defaults instead. Error: {e}")
        return dict(DEFAULT_CONFIG)
