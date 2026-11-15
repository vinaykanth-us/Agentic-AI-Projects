"""CLI for the Daily Task Planner Agent (Project 3 of 5).

Usage:
    python main.py "Finish assignment, exercise and attend meeting at 4 PM"
    python main.py                       # interactive mode

Prints the timetable, then the same schedule as JSON.
Standard library only — no API keys, no network calls.
"""

from __future__ import annotations

import json
import sys

from agent import planner_agent


def print_timetable(schedule: list[dict]) -> None:
    """Print a clean timetable, one task per line."""
    print("Your day, planned:")
    print("-" * 52)
    for item in schedule:
        print(
            f"{item['time']}  {item['task']} "
            f"({item['duration_min']} min, {item['priority']})"
        )
    print("-" * 52)
    total = sum(item["duration_min"] for item in schedule)
    print(f"{len(schedule)} tasks, {total} minutes planned.")


def run(tasks_text: str) -> list[dict]:
    """Plan the day and print the timetable + JSON. Returns the schedule."""
    schedule = planner_agent(tasks_text)
    if not schedule:
        print("No tasks found — try e.g.:")
        print('  python main.py "Finish assignment, exercise and attend meeting at 4 PM"')
        return schedule
    print_timetable(schedule)
    print()
    print("JSON:")
    print(json.dumps(schedule, indent=2))
    return schedule


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        tasks_text = " ".join(argv[1:])
    else:
        print("Daily Task Planner Agent")
        print("Enter your tasks (comma-separated), e.g.:")
        print("  Finish assignment, exercise and attend meeting at 4 PM")
        print("Press Enter on an empty line to quit.")
        try:
            tasks_text = input("\nTasks: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0
        if not tasks_text:
            print("No tasks given. Goodbye!")
            return 0
    run(tasks_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
