"""
Priority Classifier - Rule-based keyword scoring.
No training data or API needed.
"""

HIGH_KEYWORDS = [
    "asap", "urgent", "critical", "immediately", "blocker",
    "emergency", "must", "highest priority", "top priority",
    "crucial", "vital", "right away", "as soon as possible",
    "breaking", "severe", "mandatory", "deadline today",
    "cannot wait", "high priority", "important"
]

MEDIUM_KEYWORDS = [
    "soon", "needed", "should", "priority", "necessary",
    "this week", "follow up", "scheduled", "planned",
    "next sprint", "by friday", "by end of week", "moderate",
    "required", "medium priority"
]

LOW_KEYWORDS = [
    "when possible", "eventually", "nice to have", "low priority",
    "minor", "optional", "if time permits", "backlog",
    "someday", "later", "future", "consider", "maybe"
]


def classify_priority(text: str) -> str:
    text_lower = text.lower()
    high_score   = sum(1 for kw in HIGH_KEYWORDS   if kw in text_lower)
    medium_score = sum(1 for kw in MEDIUM_KEYWORDS if kw in text_lower)
    low_score    = sum(1 for kw in LOW_KEYWORDS    if kw in text_lower)

    if high_score > 0:
        return "high"
    elif medium_score > 0:
        return "medium"
    elif low_score > 0:
        return "low"
    else:
        return "medium"