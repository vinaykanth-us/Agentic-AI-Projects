"""
Email Drafting Agent — Project 4 of 5
Agentic AI Projects (from @aman_views, Instagram post De8R_m-FDtg, 25 Oct 2026)

Agent loop:
    USER REQUEST -> WRITE DRAFT -> REVIEW -> APPROVE?
        YES -> SEND (only with --send + typed "yes" + SMTP configured)
        NO  -> EDIT (revise the draft, review again)

SAFETY IS THE POINT:
    The agent NEVER sends an email automatically.
    Default behaviour is draft-only. Sending requires ALL of:
      1. the --send flag on the CLI (or auto_send=True in code), AND
      2. a typed "yes" approval from the user, AND
      3. SMTP settings provided via environment variables.
    No credentials are hardcoded anywhere. No real email is sent
    in tests or by default.

Python 3.10+ compatible. Standard library only.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

def detect_intent(instruction: str) -> str:
    """Detect the email intent from the user's request.

    Returns one of: "leave", "thank_you", "follow_up", "general".
    Matching is keyword-based and case-insensitive.
    """
    text = (instruction or "").lower()

    if any(word in text for word in ("leave", "sick day", "day off", "vacation", "time off", "absence")):
        return "leave"
    if any(word in text for word in ("thank", "thanks", "grateful", "appreciat")):
        return "thank_you"
    if any(word in text for word in ("follow up", "follow-up", "followup", "application status",
                                     "job application", "interview", "status of my")):
        return "follow_up"
    return "general"


# ---------------------------------------------------------------------------
# Draft creation
# ---------------------------------------------------------------------------

def create_email(instruction: str) -> dict:
    """Create a professional email draft for *instruction*.

    Returns a dict: {"subject": str, "body": str, "intent": str,
                     "instruction": str}

    Where a name, date, company or role is unknown, the draft uses a
    clearly marked placeholder such as [Your Name] or [Tomorrow's Date].
    The agent NEVER invents the user's name, company or dates.
    """
    intent = detect_intent(instruction)
    instruction = (instruction or "").strip()

    if intent == "leave":
        subject = "Leave Request for [Tomorrow's Date]"
        body = (
            "Dear [Manager's Name],\n"
            "\n"
            "I am writing to request leave for [Tomorrow's Date].\n"
            "\n"
            "I will make sure my current work is handed over before then, "
            "and I will be available on email if anything urgent comes up.\n"
            "\n"
            "Thank you for your understanding.\n"
            "\n"
            "Kind regards,\n"
            "[Your Name]\n"
            "[Your Phone Number]"
        )

    elif intent == "thank_you":
        subject = "Thank You — [Reason for Thanking]"
        body = (
            "Dear [Professor's Name],\n"
            "\n"
            "Thank you very much for your time and guidance. "
            "I really appreciated [what they helped you with].\n"
            "\n"
            "Your advice has helped me a lot, and I will keep working on "
            "[what you will do next].\n"
            "\n"
            "Thank you again.\n"
            "\n"
            "Kind regards,\n"
            "[Your Name]"
        )

    elif intent == "follow_up":
        subject = "Follow-Up on My Job Application for [Role]"
        body = (
            "Dear [Hiring Manager's Name],\n"
            "\n"
            "I hope you are doing well. I am writing to follow up on my "
            "application for the [Role] position at [Company Name], "
            "submitted on [Date Submitted].\n"
            "\n"
            "I remain very interested in the role and would be glad to "
            "share any further information you may need.\n"
            "\n"
            "Thank you for your time and consideration.\n"
            "\n"
            "Kind regards,\n"
            "[Your Name]\n"
            "[Your Phone Number]"
        )

    else:
        # General request: use the request itself (trimmed) as the basis
        # for the subject, without inventing any details.
        short = re.sub(r"\s+", " ", instruction).strip()
        if len(short) > 60:
            short = short[:57].rstrip() + "..."
        subject = f"Regarding: {short}" if short else "Draft Email — [Subject]"
        body = (
            "Dear [Recipient's Name],\n"
            "\n"
            "I am writing regarding: "
            f"{instruction or '[your topic]'}\n"
            "\n"
            "[Add the main point of your email here.]\n"
            "\n"
            "Thank you for your time.\n"
            "\n"
            "Kind regards,\n"
            "[Your Name]"
        )

    return {
        "subject": subject,
        "body": body,
        "intent": intent,
        "instruction": instruction,
    }


# ---------------------------------------------------------------------------
# Edit loop
# ---------------------------------------------------------------------------

def revise_draft(draft: dict, edit_instruction: str) -> dict:
    """Return a revised copy of *draft* after an edit instruction.

    The original draft is not mutated. The returned draft has
    status-friendly fields: the same subject/intent, a revised body,
    and "edited_from" recording the edit that was applied.

    Supported edits (case-insensitive, best effort):
      - "shorter" / "short"  -> keep the opening, drop the middle detail
      - "more formal"        -> "Dear" stays, "Kind regards" -> "Yours sincerely"
      - anything else        -> append the requested change as a clearly
                                marked [Edit requested: ...] line, so the
                                user can see exactly what was asked for
                                and fill it in themselves.
    """
    edit = (edit_instruction or "").strip()
    revised = dict(draft)
    body = draft["body"]
    lower = edit.lower()

    if "shorter" in lower or edit.lower() == "short" or "make it short" in lower:
        lines = [line for line in body.splitlines() if line.strip()]
        # Keep greeting, first substantive paragraph, and sign-off block.
        kept = lines[:3] + lines[-3:]
        body = "\n\n".join(kept)
    elif "more formal" in lower or "formal" in lower:
        body = body.replace("Kind regards,", "Yours sincerely,")
        body = body.replace("Hi ", "Dear ")
    else:
        body = body + f"\n\n[Edit requested: {edit}]"

    revised["body"] = body
    revised["edited_from"] = edit
    return revised


# ---------------------------------------------------------------------------
# Human approval — the safety gate
# ---------------------------------------------------------------------------

def get_user_approval(draft: dict, input_func=input) -> bool:
    """Show the draft and ask the user for approval.

    Returns True ONLY when the user types exactly "yes"
    (case-insensitive, surrounding whitespace ignored).
    Anything else — "no", "y", Enter, an empty reply — is a refusal.
    """
    print("\n--- Draft for review ---")
    print(f"Subject: {draft['subject']}")
    print()
    print(draft["body"])
    print("------------------------")
    answer = input_func("Send this email? Type 'yes' to approve, anything else to cancel: ")
    return (answer or "").strip().lower() == "yes"


# ---------------------------------------------------------------------------
# Sending (SMTP only — never automatic, never in tests)
# ---------------------------------------------------------------------------

def send_email(draft: dict, smtp_config: dict | None = None) -> bool:
    """Attempt to send *draft* via SMTP.

    Returns False (and sends nothing) when smtp_config is missing or
    incomplete. Raises no error for a missing config — the caller
    reports "sending is not configured" instead.

    smtp_config must contain: host, port, username, password,
    from_addr, to_addr. Use STARTTLS on port 587 by default.
    """
    if not smtp_config:
        return False
    required = ("host", "port", "username", "password", "from_addr", "to_addr")
    if any(not smtp_config.get(key) for key in required):
        return False

    import smtplib
    from email.message import EmailMessage

    message = EmailMessage()
    message["Subject"] = draft["subject"]
    message["From"] = smtp_config["from_addr"]
    message["To"] = smtp_config["to_addr"]
    message.set_content(draft["body"])

    with smtplib.SMTP(smtp_config["host"], int(smtp_config["port"])) as server:
        server.starttls()
        server.login(smtp_config["username"], smtp_config["password"])
        server.send_message(message)
    return True


# ---------------------------------------------------------------------------
# The agent loop
# ---------------------------------------------------------------------------

def email_agent(instruction: str, auto_send: bool = False,
                approve_fn=None, send_fn=None) -> dict:
    """Run the Email Drafting Agent for *instruction*.

    Returns a dict: {"draft": {...}, "status": str, "sent": bool}

    Status is one of:
      - "draft — awaiting approval"  (default; nothing was sent)
      - "approved"                  (user approved, but sending was
                                     not requested / not configured)
      - "sent"                      (approved AND actually sent)
      - "edited"                    (see revise_draft; returned by the
                                     edit path in main.py, not here)

    The approval gate: when auto_send is True, approval is still
    required. If the user does not approve, nothing is sent and the
    status stays "draft — awaiting approval".
    """
    draft = create_email(instruction)

    if not auto_send:
        return {"draft": draft, "status": "draft — awaiting approval", "sent": False}

    # auto_send=True still needs explicit human approval.
    approve = approve_fn if approve_fn is not None else get_user_approval
    if not approve(draft):
        return {"draft": draft, "status": "draft — awaiting approval", "sent": False}

    # Approved, but no way to send -> "approved", never pretend it sent.
    send = send_fn if send_fn is not None else send_email
    try:
        sent = bool(send(draft))
    except Exception:
        sent = False

    if sent:
        return {"draft": draft, "status": "sent", "sent": True}
    return {"draft": draft, "status": "approved", "sent": False}
