"""
Core Task Extractor - spaCy NLP pipeline.

Steps:
1. Split text into sentences
2. Filter task-like sentences (action verbs)
3. Extract owner via NER (Named Entity Recognition)
4. Extract deadline via dateparser
5. Classify priority via keywords
"""

import re
import logging
from typing import List, Dict, Any

from ml_model.priority_model import classify_priority
from ml_model.date_parser import extract_deadline

logger = logging.getLogger(__name__)

_nlp = None

ACTION_VERBS = {
    "will", "should", "must", "needs", "need", "has", "have",
    "shall", "would", "is going", "are going", "assigned",
    "complete", "finish", "deliver", "submit", "review", "create",
    "build", "design", "fix", "update", "send", "schedule",
    "prepare", "launch", "test", "deploy", "write", "implement",
    "develop", "check", "ensure", "responsible", "handle", "manage"
}

SKIP_PATTERNS = [
    r"^(we|i|everyone|all)\s+(discussed|talked|agreed|mentioned|decided)",
    r"^(the meeting|this meeting|today)",
    r"^(agenda|attendees|present|location|date|time)\s*:",
    r"^\s*$",
]


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded OK")
        except OSError:
            raise RuntimeError(
                "spaCy model not found. Run: python -m spacy download en_core_web_sm"
            )
        except ImportError:
            raise RuntimeError(
                "spaCy not installed. Run: pip install spacy"
            )
    return _nlp


def extract_tasks(meeting_text: str) -> List[Dict[str, Any]]:
    nlp = get_nlp()
    sentences = _split_sentences(meeting_text, nlp)
    tasks = []
    seen = set()

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        if _should_skip(sentence):
            continue
        if not _is_task(sentence):
            continue

        task_text = _clean_task(sentence)
        owner     = _extract_owner(sentence, nlp)
        deadline  = extract_deadline(sentence)
        priority  = classify_priority(sentence)

        key = task_text[:40].lower()
        if key in seen:
            continue
        seen.add(key)

        tasks.append({
            "task":     task_text,
            "owner":    owner,
            "deadline": deadline,
            "priority": priority,
        })

    return tasks


def _split_sentences(text: str, nlp) -> List[str]:
    sentences = []
    for line in text.replace('\r\n', '\n').split('\n'):
        line = line.strip()
        if not line:
            continue
        doc = nlp(line)
        for sent in doc.sents:
            s = sent.text.strip()
            if s:
                sentences.append(s)
    return sentences


def _should_skip(sentence: str) -> bool:
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, sentence, re.IGNORECASE):
            return True
    return False


def _is_task(sentence: str) -> bool:
    lower = sentence.lower()
    words = set(lower.split())
    if words & ACTION_VERBS:
        return True
    if re.match(r'^[-•*]\s+', sentence):
        return True
    if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*:', sentence):
        return True
    return False


def _extract_owner(sentence: str, nlp) -> str:
    doc = nlp(sentence)

    # spaCy NER - PERSON entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip().title()
            if len(name) > 1:
                return name

    # "Name will/should/needs/must" pattern
    m = re.match(
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+'
        r'(?:will|should|must|needs|has|is going|are going)',
        sentence
    )
    if m:
        return m.group(1).title()

    # "Name: task" pattern
    m = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:', sentence)
    if m:
        return m.group(1).title()

    # ORG entities (team names)
    for ent in doc.ents:
        if ent.label_ == "ORG":
            return ent.text.strip().title()

    return "Unassigned"


def _clean_task(sentence: str) -> str:
    text = re.sub(r'^[-•*]\s+', '', sentence)
    text = re.sub(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*:\s*', '', text)
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    if text and not text[-1] in '.!?':
        text += '.'
    return text