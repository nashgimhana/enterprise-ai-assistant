import re


SUSPICIOUS_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"reveal (the )?(system|developer) prompt",
    r"show (me )?(all )?restricted documents",
    r"bypass (rbac|access control|authorization)",
    r"act as (an )?admin",
    r"disable (the )?(guardrails|security)",
]


def find_prompt_injection(text: str) -> str | None:
    normalized = text.strip().lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized):
            return pattern
    return None
