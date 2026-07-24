import keyring

SERVICE_NAME = "core_shell"
ANTHROPIC_KEY_NAME = "anthropic_api_key"


def get_anthropic_key():
    """Returns the stored API key, or None if nothing is set (or the
    credential store itself can't be reached — either way, treated the
    same by callers: no key available)."""
    try:
        return keyring.get_password(SERVICE_NAME, ANTHROPIC_KEY_NAME)
    except keyring.errors.KeyringError as e:
        print(f"[credentials] Couldn't reach the credential store, treating as no key set: {e}")
        return None


def set_anthropic_key(api_key):
    """Stores the API key in the OS credential store (Keychain on macOS)."""
    keyring.set_password(SERVICE_NAME, ANTHROPIC_KEY_NAME, api_key)


def clear_anthropic_key():
    """Removes the stored key, if any."""
    try:
        keyring.delete_password(SERVICE_NAME, ANTHROPIC_KEY_NAME)
    except keyring.errors.PasswordDeleteError:
        pass  # nothing was stored — not an error
