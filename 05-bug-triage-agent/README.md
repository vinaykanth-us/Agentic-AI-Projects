# Bug Triage Agent — Project 5 of 5

**Source:** @aman_views, Instagram post `De8R_m-FDtg` (25 Oct 2026) —
"Top 5 Beginner Agentic AI Projects", Project 5: *Learn Classification & Routing*.
Part of Vinay's Agentic AI portfolio series (projects 1–4: Weather Assistant,
PDF Q&A, Daily Task Planner, Email Drafting Agent).

## What it does

Takes a bug title + description and runs the agent loop:

```
BUG REPORT → ANALYSE → CATEGORY → PRIORITY → ASSIGN TEAM
```

For each report it returns structured JSON with:

| Field | Meaning |
|---|---|
| `category` | Backend, Frontend, Payments, Database, UI/UX, Performance, Security, or Other |
| `priority` | Critical, High, Medium, or Low |
| `assign_to` | The responsible team for that category |
| `summary` | A short summary of the bug |
| `matched_keywords` | The keywords that matched, for the winning category |
| `scores` | The score for **every** category, so you can see why it won |

Classification is **transparent keyword scoring** — no black box, no LLM,
no API. A keyword matches as a whole word (or exact phrase), never as a
substring, and ties are broken by a fixed category order (Payments first,
so a payment bug that also mentions an order still goes to Payments).
A report that matches nothing is classified `Other` — never a forced
wrong guess.

### Priority rules

| Priority | Trigger keywords |
|---|---|
| **Critical** | data loss / data lost, security breach, hacked, system down, crash on startup |
| **High** | payment, checkout, crash, security, login failure, broken core flow, order stuck pending |
| **Low** | typo, spelling, colour / color, alignment, font, cosmetic |
| **Medium** | everything else (slow, error, button not working, …) |

### Teams

Payments → Payments Team · Backend → Backend Team · Frontend → Frontend Team ·
UI/UX → UI/UX Team · Database → Database Team · Performance → Performance Team ·
Security → Security Team · Other → Support Team

## Tech

- Python 3.10+ (tested on 3.12.3), VS Code friendly
- **Standard library only** — no installs needed (see `requirements.txt`)
- Deterministic: the same bug report always gives the same result

## Files

| File | What it is |
|---|---|
| `agent.py` | `classify_bug()`, `find_priority()`, `assign_team()`, `summarize()`, `bug_agent()` |
| `main.py` | CLI: single bug, `--file`, or interactive mode |
| `sample_bugs.txt` | 5 sample bug reports |
| `test_agent.py` | 7 tests (`unittest`, stdlib only) |
| `requirements.txt` | Stdlib only — nothing to install |
| `README.md` | This file |

## How to run

```bash
cd 05-bug-triage-agent

# One bug report
python main.py "Payment succeeds but order remains pending."

# All sample bugs (one per line)
python main.py --file sample_bugs.txt

# Interactive mode — type bugs, 'quit' to stop
python main.py

# Tests
python -m unittest test_agent -v
```

## Example inputs and outputs

### 1. Payment bug (the post's example)

```bash
python main.py "Payment succeeds but order remains pending."
```

```json
{
  "category": "Payments",
  "priority": "High",
  "assign_to": "Payments Team",
  "summary": "Payment succeeds but order remains pending.",
  "matched_keywords": ["payment", "order"],
  "scores": {
    "Payments": 5, "Backend": 0, "Frontend": 0, "UI/UX": 0,
    "Database": 0, "Performance": 0, "Security": 0, "Other": 0
  }
}
```

### 2. The other sample bugs

| Bug report | Category | Priority | Team | Matched keywords |
|---|---|---|---|---|
| Typo in welcome message on homepage, it says "Welcom" instead of "Welcome". | UI/UX | Low | UI/UX Team | typo, welcome |
| Dashboard takes 30 seconds to load and the page freezes when filtering large reports. | Performance | Medium | Performance Team | load, freezes, takes |
| App crashes on startup and user data is lost after the update. | Backend | Critical | Backend Team | crashes |
| Login button does nothing when clicked on mobile Safari. | Frontend | Medium | Frontend Team | button, clicked |

### 3. Unknown bug — no forced guess

```bash
python main.py "Something feels off sometimes."
```

```json
{
  "category": "Other",
  "priority": "Medium",
  "assign_to": "Support Team",
  "summary": "Something feels off sometimes.",
  "matched_keywords": [],
  "scores": { "Payments": 0, "Backend": 0, "Frontend": 0, "UI/UX": 0,
              "Database": 0, "Performance": 0, "Security": 0, "Other": 0 }
}
```

## What I learned from this project

- **Classification** — turning free text into a fixed set of labels with scoring
- **Structured JSON output** — a predictable shape other tools can consume
- **Intelligent routing** — mapping a label to the team that owns it
- **Transparent decisions** — returning scores + matched keywords so a human
  can audit why the agent chose what it chose, instead of trusting a black box
