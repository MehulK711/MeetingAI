"""
AI Service - Powered by local ML models.
No API key needed. Fully offline.
"""

import logging
from typing import List, Dict, Any

from ml_model.extractor import extract_tasks
from ml_model.priority_model import classify_priority
from ml_model.date_parser import extract_deadline

logger = logging.getLogger(__name__)


def extract_tasks_from_meeting(meeting_text: str) -> List[Dict[str, Any]]:
    if not meeting_text or not meeting_text.strip():
        raise ValueError("Meeting text cannot be empty.")
    try:
        tasks = extract_tasks(meeting_text)
        if not tasks:
            raise ValueError(
                "No actionable tasks found. Try sentences like: "
                "'John will complete the report by Friday' or "
                "'Sarah needs to fix the bug ASAP'."
            )
        logger.info(f"Extracted {len(tasks)} tasks via local ML")
        return tasks
    except ValueError:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise RuntimeError(f"Task extraction failed: {str(e)}")


def suggest_reassignment(
    task: str,
    owner: str,
    deadline: str,
    days_overdue: int,
    priority: str,
    other_owners: List[str],
) -> Dict[str, str]:
    try:
        candidates = [o for o in other_owners if o != owner and o != "Unassigned"]
        suggested = candidates[0] if candidates else owner
        reason = (
            f"{owner} is {days_overdue} day(s) overdue."
            if candidates else "No other team members available."
        )
        urgency_map = {
            "high":   "Escalate immediately to manager.",
            "medium": "Follow up within 24 hours.",
            "low":    "Reassign at next team sync.",
        }
        return {
            "suggested_owner": suggested,
            "reason": reason,
            "urgency_note": urgency_map.get(priority, "Review and reassign."),
        }
    except Exception as e:
        logger.warning(f"Reassignment failed: {e}")
        return {
            "suggested_owner": owner,
            "reason": "Could not generate suggestion.",
            "urgency_note": "Please escalate manually.",
        }