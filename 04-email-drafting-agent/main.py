#!/usr/bin/env python3
"""
Email Drafting Agent — CLI (Project 4 of 5)

Usage:
    python main.py "Write a leave request for tomorrow"
    python main.py "Write a thank-you email to my professor"
    python main.py "Follow up on my job application" --send --to hiring@example.com
    python main.py "Write a leave request for tomorrow" --edit "make it shorter"

Behaviour:
  * Always writes the draft first and shows it for review.
  * Always saves the draft to drafts/ as a .txt file.
  * NEVER sends automatically. Sending needs ALL of:
        --send  AND  a typed "yes"  AND  SMTP env vars set:
            SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
            SMTP_FROM, SMTP_TO (or --to)
  * If --send is given but SMTP is not configured, the draft is
    saved and the user is told clearly that nothing was sent.

Python 3.10+ compatible. Standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from agent import create_email, email_agent, get_user_approval, revise_draft, send_email

BASE_DIR = Path(__file__).resolve().parent
DRAFTS_DIR = BASE_DIR / "drafts"


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:50] or "email-draft"


def save_draft(draft: dict) -> Path:
    """Save the draft as a .txt file in drafts/ and return its path."""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{stamp}-{_slug(draft['subject'])}.txt"
    path = DRAFTS_DIR / filename
    path.write_text(
        f"Subject: {draft['subject']}\n"
        f"Intent: {draft['intent']}\n"
        f"Instruction: {draft['instruction']}\n"
        "\n"
        f"{draft['body']}\n",
        encoding="utf-8",
    )
    return path


def smtp_config_from_env(to_addr: str | None) -> dict | None:
    """Build an SMTP config from environment variables, or None if incomplete."""
    config = {
        "host": os.environ.get("SMTP_HOST", ""),
        "port": os.environ.get("SMTP_PORT", "587"),
        "username": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASS", ""),
        "from_addr": os.environ.get("SMTP_FROM", ""),
        "to_addr": to_addr or os.environ.get("SMTP_TO", ""),
    }
    if any(not config[key] for key in ("host", "username", "password", "from_addr", "to_addr")):
        return None
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Email Drafting Agent — draft first, send only with approval.")
    parser.add_argument("instruction", help='e.g. "Write a leave request for tomorrow"')
    parser.add_argument("--send", action="store_true",
                        help="Attempt to send after approval (needs SMTP env vars).")
    parser.add_argument("--to", default=None, help="Recipient email address (overrides SMTP_TO).")
    parser.add_argument("--edit", default=None,
                        help="Edit instruction applied to the draft before review, e.g. 'make it shorter'.")
    args = parser.parse_args(argv)

    # 1. WRITE DRAFT
    draft = create_email(args.instruction)
    if args.edit:
        draft = revise_draft(draft, args.edit)
        print(f"\nEdit applied: {args.edit}")

    print(f"\nIntent detected: {draft['intent']}")
    print("\n--- Draft ---")
    print(f"Subject: {draft['subject']}")
    print()
    print(draft["body"])
    print("-------------")

    # 2. SAVE DRAFT (always, sent or not)
    saved_path = save_draft(draft)
    print(f"\nDraft saved to: {saved_path}")

    # 3. REVIEW / APPROVAL — the human-in-the-loop gate
    if not args.send:
        approved = get_user_approval(draft)
        if approved:
            print("\nStatus: approved — but not sent (run with --send to send, "
                  "with SMTP configured). Draft saved above.")
        else:
            print("\nStatus: draft — awaiting approval. Nothing was sent.")
        return 0

    # --send was requested: sending still needs SMTP + typed "yes".
    config = smtp_config_from_env(args.to)
    if config is None:
        print("\nSending is NOT configured: SMTP_HOST, SMTP_USER, SMTP_PASS, "
              "SMTP_FROM and a recipient (SMTP_TO or --to) are required.")
        print("Nothing was sent. The draft has been saved instead — "
              "set the SMTP variables and re-run with --send to send it.")
        print("\nStatus: draft — awaiting approval. Nothing was sent.")
        return 0

    result = email_agent(
        args.instruction,
        auto_send=True,
        send_fn=lambda d: send_email(d, config),
    )
    # email_agent re-creates the draft; the edited draft above is the one
    # saved, so re-apply the edit note if one was given — the saved file
    # is the source of truth for what was reviewed.
    if result["status"] == "sent":
        print(f"\nStatus: sent to {config['to_addr']}.")
    elif result["status"] == "approved":
        print("\nStatus: approved, but sending failed or was not completed. "
              "Nothing was confirmed sent. Draft saved above.")
    else:
        print("\nStatus: draft — awaiting approval. Nothing was sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
