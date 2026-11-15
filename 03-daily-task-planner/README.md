# Daily Task Planner Agent — Project 3 of 5

A beginner-friendly Agentic AI project from the [@aman_views](https://www.instagram.com/p/De8R_m-FDtg/) Instagram post "Top 5 Beginner Agentic AI Projects" (25 Oct 2026).

Give it a natural list of tasks and it plans your day: it works out
what is fixed in time, ranks the rest by priority, estimates how
long each task takes, and builds a conflict-free timetable.

## What it does

- **Parses** a natural list — comma/newline-separated, or joined
  with "and": `"Finish assignment, exercise and attend meeting at 4 PM"`
- **Detects fixed-time tasks** — `"meeting at 4 PM"` / `"standup at 10:30"`
  stays at that time. (`"by 4 PM"` is treated as a deadline, not a
  fixed slot.)
- **Ranks by priority** — `urgent`, `asap`, `critical`, `important`,
  `deadline` → high; `optional`, `low priority`, `if time` → low;
  everything else → medium.
- **Estimates durations** — sensible defaults by task type
  (assignment 120 min, meeting 60, exercise 60, email 30, run 45…),
  or an explicit one: `"read for 30 minutes"`, `"study for 2 hours"`.
- **Builds a schedule** starting at 09:00 with no overlaps, and
  outputs a clean timetable plus a JSON version.

## The planning workflow (agent loop)

```
TASKS → PRIORITIZE → ESTIMATE TIME → BUILD SCHEDULE → CONFIRM
```

1. `parse_tasks()` — split the text into tasks, detect fixed times
   and priorities, estimate durations.
2. `rank_tasks()` — flexible tasks sorted highest priority first
   (stable: equal priorities keep their input order).
3. `estimate_duration()` — explicit duration wins, else a
   keyword-based default.
4. `create_schedule()` — fixed tasks anchored at their time, then
   ranked flexible tasks packed into the earliest free slot.
5. `planner_agent()` — runs the whole loop and returns the schedule
   as a list of `{time, task, duration_min, priority}` dicts.

## How to run

Python 3.10+ — standard library only, nothing to install.

```bash
python main.py "Finish assignment, exercise and attend meeting at 4 PM"
```

Or interactive mode:

```bash
python main.py
```

Run the tests from this folder:

```bash
python -m unittest test_agent -v
```

## Example inputs

### 1. The post's example

```bash
python main.py "Finish assignment, exercise and attend meeting at 4 PM"
```

```
Your day, planned:
----------------------------------------------------
09:00  Finish assignment (120 min, medium)
11:00  Exercise (60 min, medium)
16:00  Attend meeting (60 min, medium)
----------------------------------------------------
3 tasks, 240 minutes planned.
```

The meeting stays at 16:00; the other tasks are packed from 09:00
around it with no overlaps.

### 2. Urgent work first

```bash
python main.py "read a book, urgent assignment, exercise"
```

The urgent assignment is scheduled at 09:00, ahead of the
medium-priority tasks, even though it was listed second.

### 3. Explicit times and durations

```bash
python main.py "team standup at 10:30, study for 2 hours, reply to email, optional walk"
```

Standup is anchored at 10:30, study takes its explicit 2 hours,
and the optional walk is ranked last.

## Tech

- **Python 3.10+**, standard library only (`re`, `json`, `unittest`)
- Structured output: every schedule item is
  `{time, task, duration_min, priority}`, printed as a timetable
  and as JSON
- Deterministic: same input always gives the same schedule — no
  randomness, no external APIs, no API keys

## Files

| File | What it is |
| --- | --- |
| `agent.py` | The agent: `parse_tasks()`, `rank_tasks()`, `estimate_duration()`, `create_schedule()`, `planner_agent()` |
| `main.py` | CLI — one-liner mode or interactive mode, prints timetable + JSON |
| `test_agent.py` | 11 tests: fixed-time anchoring, no overlaps, priority ranking, parsing, durations |
| `requirements.txt` | Standard library only — nothing to install |
| `README.md` | This file |

## Key takeaway

> Break one large goal into small, ordered actions — and let the
> agent do the ordering.
