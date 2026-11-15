"""Tests for the Email Drafting Agent (Project 4 of 5).

No real email is sent in any test. Sending is only ever attempted
through an injected fake send function, never through SMTP.
Run from the project folder:
    python -m unittest test_agent -v
"""

import unittest

from agent import create_email, detect_intent, email_agent, get_user_approval, revise_draft


class TestDraftCreation(unittest.TestCase):
    def test_leave_request_draft_contains_subject_and_leave_wording(self):
        draft = create_email("Write a leave request for tomorrow")
        self.assertEqual(draft["intent"], "leave")
        self.assertIn("Leave Request", draft["subject"])
        self.assertIn("leave", draft["body"].lower())
        self.assertIn("request", draft["body"].lower())

    def test_thank_you_intent_detected(self):
        draft = create_email("Write a thank-you email to my professor")
        self.assertEqual(draft["intent"], "thank_you")
        self.assertIn("Thank You", draft["subject"])

    def test_follow_up_intent_detected(self):
        draft = create_email("Follow up on my job application")
        self.assertEqual(draft["intent"], "follow_up")
        self.assertIn("Follow-Up", draft["subject"])
        self.assertIn("application", draft["body"].lower())

    def test_detect_intent_general(self):
        self.assertEqual(detect_intent("Write an email about the meeting"), "general")


class TestPlaceholdersNotInventedDetails(unittest.TestCase):
    def test_placeholders_used_instead_of_invented_names(self):
        draft = create_email("Write a leave request for tomorrow")
        # Unknown details must be placeholders, clearly marked [...]
        self.assertIn("[Your Name]", draft["body"])
        self.assertIn("[Tomorrow's Date]", draft["subject"])
        self.assertIn("[Manager's Name]", draft["body"])

    def test_no_invented_personal_details(self):
        # The agent must not invent a name, company or date.
        for instruction in (
            "Write a leave request for tomorrow",
            "Write a thank-you email to my professor",
            "Follow up on my job application",
        ):
            draft = create_email(instruction)
            combined = draft["subject"] + "\n" + draft["body"]
            # Placeholders are present; no real-looking personal name is invented.
            self.assertIn("[", combined)
            self.assertNotIn("Vinay", combined)
            self.assertNotIn("John Smith", combined)


class TestApprovalGate(unittest.TestCase):
    def test_approval_gate_blocks_sending_when_not_approved(self):
        sent_calls = []

        def fake_send(draft):
            sent_calls.append(draft)
            return True

        result = email_agent(
            "Write a leave request for tomorrow",
            auto_send=True,
            approve_fn=lambda draft: False,  # user said no
            send_fn=fake_send,
        )
        self.assertEqual(result["status"], "draft — awaiting approval")
        self.assertFalse(result["sent"])
        self.assertEqual(sent_calls, [], "send must never be called without approval")

    def test_default_mode_never_sends(self):
        sent_calls = []
        result = email_agent(
            "Write a leave request for tomorrow",
            auto_send=False,
            send_fn=lambda draft: sent_calls.append(draft) or True,
        )
        self.assertEqual(result["status"], "draft — awaiting approval")
        self.assertFalse(result["sent"])
        self.assertEqual(sent_calls, [])

    def test_approved_and_sent_only_with_yes_and_send_fn(self):
        result = email_agent(
            "Write a leave request for tomorrow",
            auto_send=True,
            approve_fn=lambda draft: True,
            send_fn=lambda draft: True,
        )
        self.assertEqual(result["status"], "sent")
        self.assertTrue(result["sent"])

    def test_approved_but_no_send_fn_means_approved_not_sent(self):
        result = email_agent(
            "Write a leave request for tomorrow",
            auto_send=True,
            approve_fn=lambda draft: True,
            send_fn=lambda draft: False,  # e.g. SMTP not configured
        )
        self.assertEqual(result["status"], "approved")
        self.assertFalse(result["sent"])

    def test_get_user_approval_only_accepts_yes(self):
        draft = create_email("Write a leave request for tomorrow")
        self.assertTrue(get_user_approval(draft, input_func=lambda prompt: "yes"))
        self.assertTrue(get_user_approval(draft, input_func=lambda prompt: "  YES  "))
        self.assertFalse(get_user_approval(draft, input_func=lambda prompt: "y"))
        self.assertFalse(get_user_approval(draft, input_func=lambda prompt: "no"))
        self.assertFalse(get_user_approval(draft, input_func=lambda prompt: ""))


class TestEditLoop(unittest.TestCase):
    def test_revise_draft_returns_edited_copy(self):
        draft = create_email("Write a leave request for tomorrow")
        revised = revise_draft(draft, "make it shorter")
        self.assertNotEqual(revised["body"], draft["body"])
        self.assertEqual(revised["edited_from"], "make it shorter")
        # Original draft is not mutated.
        self.assertIn("handed over", draft["body"])

    def test_revise_draft_general_edit_is_marked(self):
        draft = create_email("Write a leave request for tomorrow")
        revised = revise_draft(draft, "mention my project deadline")
        self.assertIn("[Edit requested: mention my project deadline]", revised["body"])


if __name__ == "__main__":
    unittest.main()
