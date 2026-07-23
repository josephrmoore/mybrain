"""
One-time setup: stores your Anthropic API key in the macOS Keychain.

Run this once from Terminal:
    python3 set_credential.py

You'll be prompted to paste your key. It's stored securely via the OS
credential store, not written to any file in this project. You can
re-run this any time to update the key.
"""

import getpass
import credentials


def main():
    existing = credentials.get_anthropic_key()
    if existing:
        print("An API key is already stored (ending in ..." + existing[-4:] + ").")
        confirm = input("Replace it? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Left unchanged.")
            return

    key = getpass.getpass("Paste your Anthropic API key (input hidden): ").strip()
    if not key:
        print("No key entered — nothing was saved.")
        return

    credentials.set_anthropic_key(key)
    print("Key saved to the Keychain.")


if __name__ == "__main__":
    main()
