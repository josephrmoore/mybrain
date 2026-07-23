import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5:7b-instruct"
TIMEOUT_SECONDS = 30


def call(prompt, model=DEFAULT_MODEL):
    """
    Calls a local Ollama model. Returns the response text, or None if
    Ollama isn't running, the model isn't installed, or the call fails
    for any reason. Never raises — same graceful-degradation contract
    as api_client.call(), so callers can treat None as "escalate to
    the next rung on the ladder" regardless of which rung failed.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json().get("response")
    except requests.exceptions.ConnectionError:
        print("[local_llm] Ollama isn't running — skipping local LLM call.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[local_llm] Local LLM call failed, treating as unavailable: {e}")
        return None
