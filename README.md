# Agentic AI Projects — 5 Beginner Agent Projects

Five small, working Python AI agents, built in order from the
[@aman_views](https://www.instagram.com/p/De8R_m-FDtg/) Instagram post
"Top 5 Beginner Agentic AI Projects" (25 Oct 2026).

Each project is one agent loop, one core concept, and one runnable demo.
No API keys needed for any of them.

| # | Project | What it teaches | Folder | Run it |
|---|---------|-----------------|--------|--------|
| 1 | Weather Assistant Agent | Tool calling, live data | `01-weather-assistant-agent` | `python main.py "Should I carry an umbrella in Delhi?"` |
| 2 | PDF Q&A Agent | Basic RAG, chunking + retrieval | `02-pdf-qa-agent` | `python main.py sample_resume.txt "Which skills are mentioned in this resume?"` |
| 3 | Daily Task Planner Agent | Planning, structured output | `03-daily-task-planner` | `python main.py "Finish assignment, exercise and attend meeting at 4 PM"` |
| 4 | Email Drafting Agent | Human-in-the-loop, safe actions | `04-email-drafting-agent` | `python main.py "Write a leave request for tomorrow"` |
| 5 | Bug Triage Agent | Classification, priority, routing | `05-bug-triage-agent` | `python main.py "Payment succeeds but order remains pending."` |

## The agent loop

Every project follows the same shape from the post:

**GOAL → DECIDE → USE TOOL → OBSERVE → ANSWER**

- **1. Weather:** extracts the city, calls the free Open-Meteo API (no key),
  and gives advice from real numbers — it never guesses the weather.
- **2. PDF Q&A:** chunks a document, retrieves the most relevant chunks
  (TF-IDF, standard library only), and answers only from the document.
  If the answer isn't in the document, it says so.
- **3. Planner:** ranks tasks by priority/deadline, estimates time, and
  builds a conflict-free timetable from 09:00.
- **4. Email:** writes a professional draft and shows it for approval.
  It **never sends without a typed "yes"** — draft-only by default.
- **5. Bug Triage:** scores a bug report against transparent keywords,
  assigns a category, priority and team, and returns structured JSON.

## How to run

Each folder is standalone, Python 3.10+, VS Code friendly.

```bash
cd 01-weather-assistant-agent
pip install -r requirements.txt
python main.py "Should I carry an umbrella in Delhi?"
python -m unittest test_agent
```

Projects 3, 4 and 5 use only the Python standard library — nothing to install.
Project 1 needs `requests`. Project 2 needs `pypdf` (for real PDFs;
`.txt` and `.md` files work without it).

## Tests

53 unit tests in total, all passing (verified 14 Nov 2026):

| Project | Tests |
|---------|-------|
| 1. Weather Assistant | 13 |
| 2. PDF Q&A | 9 |
| 3. Daily Task Planner | 11 |
| 4. Email Drafting | 13 |
| 5. Bug Triage | 7 |

Run them per project with `python -m unittest test_agent` from that folder.

## Built by

Vinaykanth Borugadda — AI Developer & Data Analyst, Hartford, CT.
Source idea: @aman_views, "Top 5 Beginner Agentic AI Projects".
