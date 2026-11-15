"""Daily Task Planner Agent — Project 3 of 5 (Agentic AI portfolio).

Agent loop: TASKS -> PRIORITIZE -> ESTIMATE TIME -> BUILD SCHEDULE -> CONFIRM.

Takes a natural-language list of tasks, detects fixed-time tasks
(e.g. "meeting at 4 PM"), ranks the rest by priority keywords,
estimates a duration for each task, and builds a conflict-free
timetable starting at 09:00.

Python 3.10+ compatible. Standard library only — no external
APIs, no API keys, deterministic output.
"""

from __future__ import annotations

import re
from typing import Optional

START_MINUTES = 9 * 60  # 09:00

# Priority levels (higher number = more important).
PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_LOW = "low"
_PRIORITY_SCORE = {PRIORITY_HIGH: 3, PRIORITY_MEDIUM: 2, PRIORITY_LOW: 1}

_HIGH_WORDS = ("urgent", "asap", "critical", "important", "deadline", "due")
_LOW_WORDS = ("low priority", "optional", "if time", "whenever", "later")

# (keyword, default duration in minutes) — first match wins.
_DURATION_RULES = (
    ("meeting", 60),
    ("call", 30),
    ("interview", 60),
    ("assignment", 120),
    ("homework", 90),
    ("study", 60),
    ("project", 120),
    ("report", 90),
    ("essay", 120),
    ("exercise", 60),
    ("workout", 60),
    ("gym", 60),
    ("run", 45),
    ("walk", 30),
    ("yoga", 60),
    ("email", 30),
    ("read", 45),
    ("cook", 45),
    ("lunch", 45),
    ("dinner", 60),
    ("breakfast", 30),
    ("shop", 60),
    ("groceries", 60),
    ("clean", 45),
    ("laundry", 45),
)
DEFAULT_DURATION_MIN = 60

_TIME_RE = re.compile(
    r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.IGNORECASE
)
_CLOCK_RE = re.compile(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", re.IGNORECASE)
_DURATION_RE = re.compile(
    r"\b(?:for\s+)?(\d+)\s*(hours?|hrs?|minutes?|mins?)\b", re.IGNORECASE
)


def _to_minutes(hour: int, minute: int, ampm: Optional[str]) -> int:
    """Convert a 12/24-hour clock reading to minutes since midnight."""
    if ampm:
        ampm = ampm.lower()
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
    return hour * 60 + minute


def _find_fixed_time(text: str) -> Optional[int]:
    """Return fixed start time in minutes since midnight, or None.

    Only an explicit "at <time>" (or a bare clock time) counts as
    fixed. "by 4 PM" / "before 4 PM" is a deadline, not a fixed slot.
    """
    match = _TIME_RE.search(text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        return _to_minutes(hour, minute, match.group(3))
    match = _CLOCK_RE.search(text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return _to_minutes(hour, minute, match.group(3))
    return None


def _detect_priority(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in _LOW_WORDS):
        return PRIORITY_LOW
    if any(word in lowered for word in _HIGH_WORDS):
        return PRIORITY_HIGH
    return PRIORITY_MEDIUM


def _clean_task_text(text: str) -> str:
    """Tidy a task fragment: strip time/duration phrases, capitalise."""
    text = _TIME_RE.sub("", text)
    text = _CLOCK_RE.sub("", text)
    text = _DURATION_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip(" ,.;")
    if not text:
        return text
    return text[0].upper() + text[1:]


def parse_tasks(tasks_text: str) -> list[dict]:
    """Split free text into individual tasks.

    Accepts comma-, newline- and semicolon-separated lists, and
    "and"-joined tasks, e.g. "Finish assignment, exercise and
    attend meeting at 4 PM" -> three tasks.

    Each task is a dict: {task, fixed_minutes, priority, duration_min}.
    """
    if not tasks_text or not tasks_text.strip():
        return []

    fragments: list[str] = []
    for chunk in re.split(r"[,;\n]+", tasks_text):
        chunk = chunk.strip()
        if not chunk:
            continue
        # "exercise and attend meeting at 4 PM" -> two tasks.
        parts = re.split(r"\s+and\s+", chunk)
        fragments.extend(part.strip() for part in parts if part.strip())

    tasks = []
    for fragment in fragments:
        fixed = _find_fixed_time(fragment)
        tasks.append(
            {
                "task": _clean_task_text(fragment),
                "fixed_minutes": fixed,
                "priority": _detect_priority(fragment),
                "duration_min": estimate_duration(fragment),
            }
        )
    return [task for task in tasks if task["task"]]


def estimate_duration(task_text: str) -> int:
    """Estimate a task's duration in minutes.

    An explicit duration ("for 30 minutes", "2 hours") wins;
    otherwise a sensible default is chosen from the task type.
    """
    match = _DURATION_RE.search(task_text)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()
        if unit.startswith("hour") or unit.startswith("hr"):
            return value * 60
        return value
    lowered = task_text.lower()
    for keyword, minutes in _DURATION_RULES:
        if keyword in lowered:
            return minutes
    return DEFAULT_DURATION_MIN


def rank_tasks(tasks: list[dict]) -> list[dict]:
    """Rank flexible (non-fixed-time) tasks by priority, highest first.

    Fixed-time tasks are anchors, not ranked — they keep their time.
    Sorting is stable, so equal-priority tasks keep their input order.
    """
    flexible = [t for t in tasks if t["fixed_minutes"] is None]
    return sorted(
        flexible,
        key=lambda t: _PRIORITY_SCORE[t["priority"]],
        reverse=True,
    )


def _minutes_to_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _earliest_free_slot(
    occupied: list[tuple[int, int]], start: int, duration: int
) -> int:
    """Earliest start >= `start` where [start, start+duration) is free."""
    candidate = start
    for busy_start, busy_end in sorted(occupied):
        if candidate + duration <= busy_start:
            return candidate
        if candidate < busy_end:
            candidate = busy_end
    return candidate


def create_schedule(tasks: list[dict], start_hour: int = 9) -> list[dict]:
    """Build a conflict-free timetable from parsed tasks.

    Fixed-time tasks are placed at their time; flexible tasks are
    ranked by priority and packed into the earliest free slot from
    `start_hour` (default 09:00). Returns a list of dicts, sorted
    by start time: {time, task, duration_min, priority}.
    """
    day_start = start_hour * 60
    occupied: list[tuple[int, int]] = []
    scheduled: list[dict] = []

    # 1. Anchor fixed-time tasks first.
    fixed = sorted(
        (t for t in tasks if t["fixed_minutes"] is not None),
        key=lambda t: t["fixed_minutes"],
    )
    for task in fixed:
        start = max(task["fixed_minutes"], day_start)
        # If two fixed tasks overlap, push the later one to the first
        # free slot after the clash (the earlier one keeps its time).
        start = _earliest_free_slot(occupied, start, task["duration_min"])
        occupied.append((start, start + task["duration_min"]))
        scheduled.append(
            {
                "time": _minutes_to_time(start),
                "task": task["task"],
                "duration_min": task["duration_min"],
                "priority": task["priority"],
            }
        )

    # 2. Pack ranked flexible tasks into the earliest free slots.
    for task in rank_tasks(tasks):
        start = _earliest_free_slot(occupied, day_start, task["duration_min"])
        occupied.append((start, start + task["duration_min"]))
        scheduled.append(
            {
                "time": _minutes_to_time(start),
                "task": task["task"],
                "duration_min": task["duration_min"],
                "priority": task["priority"],
            }
        )

    scheduled.sort(key=lambda item: item["time"])
    return scheduled


def planner_agent(tasks_text: str) -> list[dict]:
    """Full agent loop: TASKS -> PRIORITIZE -> ESTIMATE -> SCHEDULE.

    Returns the timetable as a list of dicts with keys
    {time, task, duration_min, priority}.
    """
    tasks = parse_tasks(tasks_text)
    return create_schedule(tasks)


if __name__ == "__main__":
    import json

    demo = "Finish assignment, exercise and attend meeting at 4 PM"
    print(json.dumps(planner_agent(demo), indent=2))
