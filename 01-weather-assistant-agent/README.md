# 🌦️ Weather Assistant Agent

**Project 1 of 5 — Beginner Agentic AI Projects**
Source idea: [@aman_views](https://www.instagram.com/p/De8R_m-FDtg/) Instagram post (25 Oct 2026), “Top 5 Beginner Agentic AI Projects” — Project 1: Learn Tool Calling.

A real, working Python agent that answers natural weather questions with **real live data** — it never guesses the weather.

## What it does

Ask a question in plain English, for example:

> “Should I carry an umbrella in Delhi?”

The agent:

1. **Understands the goal** — a weather question.
2. **Decides** it needs a tool (it cannot know live weather from memory).
3. **Uses tools** — the free Open-Meteo Geocoding API to find the city, then the free Open-Meteo Forecast API for current weather and hourly precipitation probability.
4. **Observes** the real numbers returned (temperature, condition, rain chance, humidity, wind).
5. **Answers** with practical advice — umbrella, jacket, light clothes — based on those numbers.

## The agent loop

```
GOAL → DECIDE → USE TOOL → OBSERVE → ANSWER
  ↑                                        |
  └────────── (next question) ─────────────┘

USER QUESTION → EXTRACT CITY → WEATHER API → ADVICE
```

Key takeaway from the source post: **the agent does not guess the weather — it calls a tool.**

## Tech

- **Python 3.10+** (tested on Python 3.12)
- **`requests`** — the only dependency
- **Open-Meteo Geocoding API** — city → latitude/longitude
- **Open-Meteo Forecast API** — current weather + hourly precipitation probability
- **No API key needed** for either API
- **No LLM API required** — there is an optional, clearly labelled LLM hook in `agent.py` (`ask_llm_to_rephrase_advice`), which is never called by default

## How to run

```bash
cd 01-weather-assistant-agent
pip install -r requirements.txt

# One question
python main.py "Should I carry an umbrella in Delhi?"

# Interactive mode — keep asking until you type quit
python main.py
```

## Example questions (expected behaviour)

| Question | What happens |
|---|---|
| `Should I carry an umbrella in Delhi?` | Extracts **Delhi**, calls Open-Meteo, reports the real temperature/condition/rain chance, and says yes/no to the umbrella based on the real rain chance (≥50% or rainy condition → “Yes, carry an umbrella”). |
| `What's the weather in New York tomorrow?` | Extracts **New York** (multi-word city), reports live weather for New York, with clothing advice from the real temperature. |
| `Is it cold today?` | No city found → defaults to **Hartford, CT**, reports live Hartford weather and jacket advice if it is cold (<10 °C). |

## Files

| File | What it is |
|---|---|
| `agent.py` | The agent: `extract_city()`, `get_weather()` (the tool), `create_advice()`, `weather_agent()` (the full loop). |
| `main.py` | CLI: one-question mode and interactive mode, with clear readable output. |
| `requirements.txt` | Only `requests==2.31.0`. |
| `test_agent.py` | Tests for city extraction, advice logic on fake data, and live-API smoke tests (skip gracefully offline). |
| `README.md` | This file. |

## Tests

```bash
python3 -m pytest test_agent.py -v
# or
python3 -m unittest test_agent -v
```

## Error handling

- Unknown city (e.g. a typo) → a clear message: “Could not find a place called … Check the spelling and try again.”
- No internet / API unreachable → a clear message, no traceback crash in the CLI.
- The live-API tests skip gracefully when offline instead of failing.

## What you learn

- Tool calling
- Real-time data
- Structured results
- The agent loop: goal → decide → use tool → observe → answer
