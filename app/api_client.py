import credentials
import events

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 1000


def call(prompt, model=DEFAULT_MODEL, max_tokens=DEFAULT_MAX_TOKENS):
    """
    The single choke point for every Claude API call in this system.

    Returns the response text, or None if the call couldn't be made
    (no key configured, or the call failed for any reason). Never raises —
    callers should treat a None return as "escalate to the next rung on
    the ladder" (e.g. quarantine for human review), not as a crash.
    """
    api_key = credentials.get_anthropic_key()
    if not api_key:
        events.log("api_client", "No Anthropic API key configured — skipping call.")
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception as e:
        events.log("api_client", f"API call failed, treating as unavailable: {e}")
        return None
