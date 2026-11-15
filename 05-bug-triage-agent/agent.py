"""
Bug Triage Agent — Project 5 of 5
Agentic AI Projects (from @aman_views, Instagram post De8R_m-FDtg)

Agent loop:
    BUG REPORT -> ANALYSE -> CATEGORY -> PRIORITY -> ASSIGN TEAM

Rule-based, deterministic, stdlib-only. No LLM, no API, no API keys.
Classification is transparent keyword scoring: every score and every
matched keyword is returned in the output, so nothing is a black box.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Keyword tables: category -> {keyword/phrase: weight}
# Order matters: it is the tie-break order when two categories score equal.
# Payments is first so a payment bug that also mentions the backend or an
# order is still routed to Payments.
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "Payments": {
        "payment": 3, "payments": 3, "checkout": 3, "billing": 3,
        "refund": 3, "transaction": 3, "invoice": 2, "order": 2,
        "purchase": 2, "card": 2, "subscription": 2, "paid": 2,
        "charged": 2, "wallet": 2,
    },
    "Backend": {
        "api": 3, "server": 3, "endpoint": 3, "backend": 3,
        "500": 3, "crash": 2, "crashes": 2, "crashed": 2,
        "internal error": 3, "service": 2, "logic": 2,
        "webhook": 2, "integration": 2, "request": 1, "response": 1,
    },
    "Frontend": {
        "button": 3, "frontend": 3, "dropdown": 2, "modal": 2,
        "click": 2, "clicked": 2, "clicking": 2, "form": 2,
        "link": 2, "navigation": 2, "menu": 2, "page": 2,
        "screen": 1, "scroll": 1,
    },
    "UI/UX": {
        "typo": 3, "spelling": 3, "colour": 3, "color": 3,
        "alignment": 3, "font": 2, "label": 2, "welcome": 1,
        "text": 1, "cosmetic": 2,
    },
    "Database": {
        "database": 3, "db": 3, "sql": 3, "query": 2,
        "record": 2, "records": 2, "stored": 2, "save": 2,
        "saved": 2, "migration": 2, "table": 2,
        "data loss": 3, "data lost": 3, "lost data": 3,
        "lost": 2,
    },
    "Performance": {
        "slow": 3, "slowly": 3, "loading": 3, "load": 3, "lag": 3,
        "lags": 3, "laggy": 3, "performance": 3, "freeze": 2,
        "freezes": 2, "frozen": 2, "timeout": 2, "takes": 1,
    },
    "Security": {
        "security": 3, "password": 3, "hacked": 3, "breach": 3,
        "vulnerability": 3, "unauthorized": 3, "unauthorised": 3,
        "xss": 3, "csrf": 3, "leak": 2, "leaked": 2,
        "login": 2, "auth": 2, "token": 2,
        "security breach": 3,
    },
}

CATEGORY_ORDER = list(CATEGORY_KEYWORDS) + ["Other"]

TEAM_BY_CATEGORY = {
    "Payments": "Payments Team",
    "Backend": "Backend Team",
    "Frontend": "Frontend Team",
    "UI/UX": "UI/UX Team",
    "Database": "Database Team",
    "Performance": "Performance Team",
    "Security": "Security Team",
    "Other": "Support Team",
}

# Priority keywords — checked in this order: Critical > High > Low > Medium.
# Low is checked after High so a typo on a payment page is still High,
# while a plain typo with no impact keywords stays Low.
CRITICAL_PHRASES = [
    "data loss", "data lost", "data is lost", "lost data", "losing data",
    "security breach", "hacked", "system down", "outage",
    "crash on startup", "crashes on startup", "crashes on launch",
    "data deleted", "deleted data",
]

HIGH_KEYWORDS = [
    "payment", "payments", "checkout", "crash", "crashes", "crashed",
    "security", "breach", "password", "leaked", "leak",
    "order remains pending", "unable to", "cannot log in", "can't log in",
    "cannot login", "fails", "failed", "not working", "broken",
    "data loss", "data lost",
]

LOW_KEYWORDS = [
    "typo", "spelling", "colour", "color", "alignment", "font",
    "cosmetic", "minor",
]

MEDIUM_KEYWORDS = [
    "slow", "loading", "lag", "error", "button", "page",
]


def _normalise(bug) -> str:
    """Accept a string, or a dict with title/description, and return text."""
    if isinstance(bug, dict):
        parts = [str(bug.get("title", "")), str(bug.get("description", ""))]
        return " ".join(p for p in parts if p).strip()
    return str(bug).strip()


def _score_categories(text: str):
    """Score every category against the text.

    Returns (scores, matched):
      scores  — {category: int} for every category, in CATEGORY_ORDER.
      matched — {category: [keyword, ...]} actually matched, in table order.
    A keyword matches as a whole word (or exact phrase), never as a
    substring — so "card" does not match "cardinal".
    """
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z0-9]+", lowered))
    scores = {category: 0 for category in CATEGORY_ORDER}
    matched = {category: [] for category in CATEGORY_ORDER}

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword, weight in keywords.items():
            if " " in keyword:
                hit = keyword in lowered
            else:
                hit = keyword in tokens
            if hit:
                scores[category] += weight
                matched[category].append(keyword)

    return scores, matched


def classify_bug(bug) -> str:
    """Return the best category for a bug report, or "Other".

    Highest keyword score wins; ties go to the earlier category in
    CATEGORY_ORDER. No keywords matched at all -> "Other", never a
    forced wrong guess.
    """
    text = _normalise(bug)
    if not text:
        return "Other"
    scores, _matched = _score_categories(text)
    best = max(CATEGORY_ORDER[:-1], key=lambda c: scores[c])
    return best if scores[best] > 0 else "Other"


def find_priority(bug, category: str | None = None) -> str:
    """Return Critical / High / Medium / Low from impact keywords.

    Critical: data loss, security breach, system down, crash on startup.
    High:     payment, crash, security, login failure, broken core flow.
    Low:      typo, spelling, colour, alignment, cosmetic.
    Medium:   everything else (including slow / error / button bugs).
    """
    text = _normalise(bug).lower()
    if not text:
        return "Medium"

    for phrase in CRITICAL_PHRASES:
        if phrase in text:
            return "Critical"
    for keyword in HIGH_KEYWORDS:
        if keyword in text:
            return "High"
    for keyword in LOW_KEYWORDS:
        if keyword in text:
            return "Low"
    for keyword in MEDIUM_KEYWORDS:
        if keyword in text:
            return "Medium"
    return "Medium"


def assign_team(category: str) -> str:
    """Return the responsible team for a category."""
    return TEAM_BY_CATEGORY.get(category, "Support Team")


def summarize(bug, category: str | None = None, priority: str | None = None) -> str:
    """Return a short summary: the bug text, cleaned and truncated.

    Takes the first sentence when the report is long, otherwise the
    whole report, capped at 120 characters on a word boundary.
    """
    text = " ".join(_normalise(bug).split())
    if not text:
        return "No bug description provided."
    # First sentence, if that already says what the bug is.
    first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    summary = first if len(first) >= 20 else text
    if len(summary) > 120:
        summary = summary[:117].rsplit(" ", 1)[0] + "..."
    return summary


def bug_agent(bug) -> dict:
    """Run the full triage loop on one bug report.

    Returns structured JSON-ready data:
        {
          "category": str,
          "priority": str,
          "assign_to": str,
          "summary": str,
          "matched_keywords": [str, ...],   # for the winning category
          "scores": {category: int, ...},   # every category, in order
        }
    """
    text = _normalise(bug)
    category = classify_bug(text)
    priority = find_priority(text, category)
    scores, matched = _score_categories(text)
    return {
        "category": category,
        "priority": priority,
        "assign_to": assign_team(category),
        "summary": summarize(text, category, priority),
        "matched_keywords": matched.get(category, []),
        "scores": scores,
    }
