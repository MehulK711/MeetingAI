"""
Deadline Extractor - Uses dateparser + regex patterns.
Extracts natural language dates from text.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import dateparser
    DATEPARSER_AVAILABLE = True
except ImportError:
    DATEPARSER_AVAILABLE = False
    logger.warning("dateparser not installed. Using fallback date logic.")


def extract_deadline(text: str, default_days: int = 7) -> str:
    text_lower = text.lower()

    # Relative pattern matching
    if any(p in text_lower for p in ["end of week", "by friday", "this friday"]):
        return _next_weekday(4)
    if any(p in text_lower for p in ["by monday", "next monday"]):
        return _next_weekday(0, next_week=True)
    if "tomorrow" in text_lower:
        return _days_from_now(1)
    if "next week" in text_lower:
        return _days_from_now(7)
    if "end of month" in text_lower:
        return _end_of_month()
    if "end of day" in text_lower or "eod" in text_lower:
        return _days_from_now(0)

    # "in X days/weeks"
    m = re.search(r'in (\d+)\s+days?', text_lower)
    if m:
        return _days_from_now(int(m.group(1)))
    m = re.search(r'in (\d+)\s+weeks?', text_lower)
    if m:
        return _days_from_now(int(m.group(1)) * 7)
    m = re.search(r'within (\d+)\s+days?', text_lower)
    if m:
        return _days_from_now(int(m.group(1)))

    # Try dateparser on full text
    if DATEPARSER_AVAILABLE:
        date_phrases = re.findall(
            r'\b(?:by|before|on|due|until)?\s*([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)\b',
            text, re.IGNORECASE
        )
        for phrase in date_phrases:
            try:
                parsed = dateparser.parse(
                    phrase.strip(),
                    settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': False}
                )
                if parsed and parsed.date() >= datetime.now().date():
                    return parsed.strftime("%Y-%m-%d")
            except Exception:
                continue

        # Try parsing full sentence
        try:
            parsed = dateparser.parse(
                text,
                settings={'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': False}
            )
            if parsed and parsed.date() >= datetime.now().date():
                return parsed.strftime("%Y-%m-%d")
        except Exception:
            pass

    return _days_from_now(default_days)


def _days_from_now(n: int) -> str:
    return (datetime.now() + timedelta(days=n)).strftime("%Y-%m-%d")


def _next_weekday(weekday: int, next_week: bool = False) -> str:
    today = datetime.now()
    days_ahead = weekday - today.weekday()
    if days_ahead <= 0 or next_week:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _end_of_month() -> str:
    today = datetime.now()
    if today.month == 12:
        end = datetime(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
    return end.strftime("%Y-%m-%d")