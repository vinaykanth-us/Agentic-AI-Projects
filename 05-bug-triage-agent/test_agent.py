"""Tests for the Bug Triage Agent (Project 5 of 5).

Run from the project folder:
    python -m unittest test_agent -v
    python test_agent.py
"""

import unittest

from agent import assign_team, bug_agent, classify_bug, find_priority, summarize


class TestBugTriageAgent(unittest.TestCase):
    def test_payment_bug_is_payments_and_high(self):
        """The post's example: payment succeeds, order stays pending."""
        result = bug_agent("Payment succeeds but order remains pending.")
        self.assertIn(result["category"], ("Payments", "Backend"))
        self.assertEqual(result["category"], "Payments")
        self.assertEqual(result["priority"], "High")
        self.assertEqual(result["assign_to"], "Payments Team")
        self.assertIn("payment", result["matched_keywords"])
        self.assertGreater(result["scores"]["Payments"], 0)

    def test_ui_typo_bug_is_low_priority(self):
        result = bug_agent(
            'Typo in welcome message on homepage, it says "Welcom" instead of "Welcome".'
        )
        self.assertIn(result["category"], ("UI/UX", "Frontend"))
        self.assertEqual(result["priority"], "Low")
        self.assertIn("typo", result["matched_keywords"])

    def test_crash_and_data_loss_bug_is_high_or_critical(self):
        result = bug_agent("App crashes on startup and user data is lost after the update.")
        self.assertIn(result["priority"], ("High", "Critical"))
        self.assertEqual(result["priority"], "Critical")
        self.assertTrue(result["summary"])

    def test_unknown_bug_is_other_not_a_forced_guess(self):
        result = bug_agent("Something feels off sometimes.")
        self.assertEqual(result["category"], "Other")
        self.assertEqual(result["matched_keywords"], [])
        self.assertEqual(result["assign_to"], "Support Team")
        self.assertEqual(result["priority"], "Medium")

    def test_performance_bug(self):
        result = bug_agent(
            "Dashboard takes 30 seconds to load and the page freezes "
            "when filtering large reports."
        )
        self.assertEqual(result["category"], "Performance")
        self.assertEqual(result["assign_to"], "Performance Team")
        self.assertEqual(result["priority"], "Medium")

    def test_helpers_agree_with_bug_agent(self):
        bug = "Payment succeeds but order remains pending."
        self.assertEqual(classify_bug(bug), "Payments")
        self.assertEqual(find_priority(bug), "High")
        self.assertEqual(assign_team("Payments"), "Payments Team")
        self.assertIn("Payment", summarize(bug))

    def test_empty_bug_is_other_and_medium(self):
        result = bug_agent("")
        self.assertEqual(result["category"], "Other")
        self.assertEqual(result["priority"], "Medium")


if __name__ == "__main__":
    unittest.main(verbosity=2)
