import local_llm
import api_client
import events


def escalate(rule_fn=None, llm_prompt=None, context=None):
    """
    The shared escalation ladder every module routes through for a fuzzy
    decision: deterministic rule -> local LLM -> Claude API -> human review.

    rule_fn: optional zero-arg callable. Return a non-None result if the
        rule resolves it, or None/omit to fall through to the LLM rungs.
    llm_prompt: the prompt to send to local/API models if the rule doesn't
        resolve it. If omitted, skips straight to human review after the rule.
    context: optional short string describing what's being decided, used
        only for the event log (e.g. "classify file: report.pdf").

    Returns {"result": ..., "decided_by": "local" | "local_llm" | "api" | "human"}.
    "decided_by" deliberately uses the same vocabulary as a module's
    handler_type — both describe the same four-way idea (where did this
    answer come from), just at different scopes: handler_type is a
    per-module registration fact, decided_by is a per-call runtime fact.
    A result of None with decided_by "human" means nothing in the ladder
    could resolve it — the calling module decides what "needs human
    review" means in its own context (e.g. quarantine a file).
    """
    if rule_fn:
        try:
            rule_result = rule_fn()
        except Exception as e:
            events.log("router", f"rule_fn raised an error, treating as inconclusive and falling through: {e}")
            rule_result = None
        if rule_result is not None:
            _log_decision(context, "local", rule_result)
            return {"result": rule_result, "decided_by": "local"}

    if llm_prompt:
        local_result = local_llm.call(llm_prompt)
        if local_result is not None:
            _log_decision(context, "local_llm", local_result)
            return {"result": local_result, "decided_by": "local_llm"}

        api_result = api_client.call(llm_prompt)
        if api_result is not None:
            _log_decision(context, "api", api_result)
            return {"result": api_result, "decided_by": "api"}

    _log_decision(context, "human", None)
    return {"result": None, "decided_by": "human"}


def _log_decision(context, decided_by, result):
    events.emit("router_decision", {
        "context": context,
        "decided_by": decided_by,
        "result_preview": (str(result)[:100] if result is not None else None),
    })
