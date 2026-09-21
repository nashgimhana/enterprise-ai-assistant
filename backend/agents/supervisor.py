from backend.security.auth import can_run_analysis


ANALYSIS_WORDS = {"analyze", "compare", "trend", "recurring", "common", "all incidents", "summarize all"}


def route_request(message: str, role: str) -> tuple[str, list[str]]:
    lowered = message.lower()
    wants_analysis = any(word in lowered for word in ANALYSIS_WORDS)
    activity = ["Request validated", "Supervisor inspected intent"]

    if wants_analysis:
        if can_run_analysis(role):
            activity.append("Supervisor selected analysis route")
            return "analysis", activity
        activity.append("Supervisor blocked analysis for this role")
        return "forbidden_analysis", activity

    activity.append("Supervisor selected retrieval route")
    return "retrieval", activity
