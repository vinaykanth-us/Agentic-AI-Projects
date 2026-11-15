"""Tests for the Daily Task Planner Agent (Project 3 of 5).

Run from this folder:
    python -m unittest test_agent -v
"""

import unittest

from agent import (
    create_schedule,
    estimate_duration,
    parse_tasks,
    planner_agent,
    rank_tasks,
)


def _to_minutes(time_str: str) -> int:
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


class TestFixedTimeTasks(unittest.TestCase):
    def test_fixed_time_task_stays_at_its_time(self):
        schedule = planner_agent(
            "Finish assignment, exercise and attend meeting at 4 PM"
        )
        meeting = next(
            item for item in schedule if "meeting" in item["task"].lower()
        )
        self.assertEqual(meeting["time"], "16:00")

    def test_fixed_time_with_24h_clock(self):
        schedule = planner_agent("Team standup at 10:30, write report")
        standup = next(
            item for item in schedule if "standup" in item["task"].lower()
        )
        self.assertEqual(standup["time"], "10:30")


class TestNoOverlaps(unittest.TestCase):
    def test_no_two_tasks_overlap(self):
        schedule = planner_agent(
            "Finish assignment, exercise and attend meeting at 4 PM, "
            "urgent email reply, read for 30 minutes"
        )
        intervals = sorted(
            (_to_minutes(item["time"]), _to_minutes(item["time"]) + item["duration_min"])
            for item in schedule
        )
        for (start_a, end_a), (start_b, _end_b) in zip(intervals, intervals[1:]):
            self.assertGreaterEqual(start_b, end_a)

    def test_flexible_tasks_start_at_09_00(self):
        schedule = planner_agent("Finish assignment, exercise")
        self.assertEqual(schedule[0]["time"], "09:00")


class TestPriorityRanking(unittest.TestCase):
    def test_priority_ranking_puts_urgent_tasks_first(self):
        tasks = parse_tasks("read a book, urgent assignment, exercise")
        ranked = rank_tasks(tasks)
        self.assertEqual(ranked[0]["task"], "Urgent assignment")
        self.assertEqual(ranked[0]["priority"], "high")

    def test_low_priority_task_ranked_last(self):
        tasks = parse_tasks("optional walk, urgent email reply, study")
        ranked = rank_tasks(tasks)
        self.assertEqual(ranked[-1]["priority"], "low")


class TestParsingAndEstimates(unittest.TestCase):
    def test_parse_splits_comma_and_and_lists(self):
        tasks = parse_tasks(
            "Finish assignment, exercise and attend meeting at 4 PM"
        )
        self.assertEqual(len(tasks), 3)
        self.assertEqual(
            [t["task"] for t in tasks],
            ["Finish assignment", "Exercise", "Attend meeting"],
        )

    def test_estimate_duration_by_task_type(self):
        self.assertEqual(estimate_duration("Finish assignment"), 120)
        self.assertEqual(estimate_duration("Go for a run"), 45)
        self.assertEqual(estimate_duration("Reply to email"), 30)

    def test_explicit_duration_wins(self):
        self.assertEqual(estimate_duration("Read for 30 minutes"), 30)
        self.assertEqual(estimate_duration("Study for 2 hours"), 120)

    def test_planner_returns_schedule_dicts(self):
        schedule = planner_agent("Finish assignment, exercise")
        self.assertEqual(len(schedule), 2)
        for item in schedule:
            self.assertEqual(
                set(item), {"time", "task", "duration_min", "priority"}
            )


class TestCreateSchedule(unittest.TestCase):
    def test_schedule_is_sorted_by_time(self):
        schedule = create_schedule(
            parse_tasks("Attend meeting at 4 PM, finish assignment, exercise")
        )
        times = [item["time"] for item in schedule]
        self.assertEqual(times, sorted(times))


if __name__ == "__main__":
    unittest.main()
