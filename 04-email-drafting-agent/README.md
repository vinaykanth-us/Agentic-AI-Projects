# 📧 Email Drafting Agent — Project 4 of 5

**Agentic AI Projects** · from @aman_views, Instagram post `De8R_m-FDtg`, 25 Oct 2026
**What it teaches:** human approval and safe execution

## What it does

You give it a request in plain English — for example *"Write a leave request for tomorrow"* — and the agent:

1. Detects the intent (leave request, thank-you, job-application follow-up, or general)
2. Picks a professional template and writes a draft (subject + body)
3. Shows the draft to you for review
4. Sends **only** if you approve — otherwise the draft is saved and nothing is sent

Where a name, date, company or role is unknown, the draft uses a clearly marked placeholder such as `[Your Name]`, `[Tomorrow's Date]` or `[Company Name]`. The agent **never invents** your name, company or dates.

## The workflow

```
USER REQUEST → WRITE DRAFT → REVIEW → APPROVE?
                                        ├─ YES → SEND
                                        └─ NO  → EDIT → REVIEW again
```

## ⚠️ Safety rule

**The agent never sends an email automatically.**

Sending requires **all three** of these at once:

1. the `--send` flag, **and**
2. you typing `yes` at the approval prompt, **and**
3. SMTP settings provided via environment variables (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, and a recipient via `SMTP_TO` or `--to`).

By default it is **draft-only**: it writes the draft, shows it, asks for approval, and saves it to `drafts/`. No credentials are hardcoded anywhere, and no real email is sent in tests or by default.

## Tech

- Python 3.10+ (tested with Python 3.12)
- Standard library only — no third-party packages, no API keys

## How to run

```bash
cd 04-email-drafting-agent

# Draft only (default — safe)
python main.py "Write a leave request for tomorrow"

# Draft, then edit it before review
python main.py "Write a leave request for tomorrow" --edit "make it shorter"

# Draft and attempt to send (needs SMTP env vars + typed "yes")
SMTP_HOST=smtp.example.com SMTP_PORT=587 SMTP_USER=you@example.com \
SMTP_PASS='...' SMTP_FROM=you@example.com \
python main.py "Follow up on my job application" --send --to hiring@example.com
```

If `--send` is given but SMTP is not configured, the agent says so clearly, saves the draft, and sends nothing.

## Example requests

| Request | Intent detected |
|---|---|
| Write a leave request for tomorrow | leave |
| Write a thank-you email to my professor | thank_you |
| Follow up on my job application | follow_up |
| Write an email about the meeting | general |

## Files

| File | What it is |
|---|---|
| `agent.py` | `create_email()`, `detect_intent()`, `revise_draft()`, `get_user_approval()`, `send_email()`, `email_agent()` — the agent loop |
| `main.py` | CLI: prints the draft, asks for approval, saves it to `drafts/` |
| `test_agent.py` | Tests — run with `python -m unittest test_agent -v` |
| `requirements.txt` | Standard library only |
| `drafts/` | Saved drafts (`.txt`), created on each run |

## Run the tests

```bash
python -m unittest test_agent -v
```
