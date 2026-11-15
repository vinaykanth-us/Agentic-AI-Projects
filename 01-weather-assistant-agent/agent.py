"""
Weather Assistant Agent — Project 1 of 5: Beginner Agentic AI Projects
Source idea: @aman_views Instagram post De8R_m-FDtg (25 Oct 2026)
"Top 5 Beginner Agentic AI Projects" — Project 1: Learn Tool Calling

Agent loop:
    GOAL -> DECIDE -> USE TOOL -> OBSERVE -> ANSWER

The agent does NOT guess the weather. It:
  1. Understands the goal (a weather question).
  2. Decides it needs a tool (it cannot answer from memory).
  3. Uses tools: Open-Meteo Geocoding API, then Open-Meteo Forecast API.
  4. Observes the real numbers returned by those tools.
  5. Answers with practical advice based on those real numbers.

No API key is needed. No LLM API is required.
An optional LLM hook is included at the bottom, clearly labelled OPTIONAL,
and is never called by weather_agent() unless the caller opts in.
"""

from __future__ import annotations

import re

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_CITY = "Hartford"

# Words that can follow a city name in a question and are NOT part of it.
_STOP_WORDS = {
    "tomorrow", "today", "tonight", "yesterday", "weekend", "morning",
    "afternoon", "evening", "night", "please", "now", "later", "next",
    "week", "this", "that", "there", "here",
}

# Common multi-word / well-known cities, checked first (longest first).
# This makes "New York", "Los Angeles", "San Francisco" etc. reliable
# even when they appear without "in" in front of them.
_KNOWN_CITIES = [
    "New York", "Los Angeles", "San Francisco", "Las Vegas",
    "Salt Lake City", "Kansas City", "New Orleans", "San Diego",
    "San Antonio", "San Jose", "New Delhi", "Mexico City",
    "Rio de Janeiro", "Sao Paulo", "Buenos Aires", "Cape Town",
    "Hong Kong", "Ho Chi Minh City",
    "Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Bangalore",
    "Hyderabad", "Pune", "Jaipur", "Lucknow", "Hartford", "Boston",
    "Chicago", "Houston", "Phoenix", "Seattle", "Denver", "Atlanta",
    "Miami", "Dallas", "Austin", "Portland", "London", "Paris",
    "Berlin", "Madrid", "Rome", "Toronto", "Vancouver", "Montreal",
    "Sydney", "Melbourne", "Tokyo", "Osaka", "Seoul", "Beijing",
    "Shanghai", "Singapore", "Dubai", "Dublin", "Edinburgh",
    "Manchester", "Birmingham", "Amsterdam", "Vienna", "Zurich",
    "Geneva", "Stockholm", "Oslo", "Copenhagen", "Helsinki",
    "Auckland", "Wellington", "Perth", "Brisbane", "Adelaide",
    "Manchester", "Leeds", "Glasgow", "Bristol", "Nairobi",
    "Lagos", "Cairo", "Tel Aviv", "Jerusalem", "Moscow",
    "Istanbul", "Athens", "Lisbon", "Barcelona", "Milan",
    "Naples", "Munich", "Hamburg", "Frankfurt", "Krakow",
    "Warsaw", "Prague", "Budapest", "Bangkok", "Jakarta",
    "Manila", "Kuala Lumpur", "Hanoi", "Karachi", "Lahore",
    "Islamabad", "Dhaka", "Kathmandu", "Colombo", "Thimphu",
]

# WMO weather codes returned by Open-Meteo.
# https://open-meteo.com/en/docs#weathervariables
_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _clean_city(raw: str) -> str:
    """Strip punctuation and trailing stop-words, then title-case."""
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", raw)
    while words and words[-1].lower() in _STOP_WORDS:
        words.pop()
    while words and words[0].lower() in {"in", "for", "at", "near", "around"}:
        words.pop(0)
    if not words:
        return ""
    # Keep at most 3 words: a city name is rarely longer.
    return " ".join(w.title() for w in words[:3])


def extract_city(question: str) -> str:
    """
    Extract the city name from a natural-language question.

    Handles multi-word cities ("New York", "Los Angeles") and
    lower-case input ("in delhi?"). Returns DEFAULT_CITY ("Hartford")
    when no city can be found.

    Examples:
        "Should I carry an umbrella in Delhi?" -> "Delhi"
        "What's the weather in New York tomorrow?" -> "New York"
        "Is it cold today?" -> "Hartford"
    """
    if not question or not question.strip():
        return DEFAULT_CITY

    text = question.strip()

    # 1. Known cities first — longest match wins, case-insensitive.
    lowered = text.lower()
    for city in sorted(_KNOWN_CITIES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(city.lower()) + r"\b", lowered):
            return city

    # 2. "in / for / at / near <city>" — the most common phrasing.
    match = re.search(
        r"\b(?:in|for|at|near|around)\s+([A-Za-z][A-Za-z\-']*(?:\s+[A-Za-z][A-Za-z\-']*){0,2})",
        text,
        re.IGNORECASE,
    )
    if match:
        city = _clean_city(match.group(1))
        if city:
            return city

    # 3. Capitalised word sequence (e.g. "Weather in Delhi" was missed
    #    above, or "Delhi weather?"). Skip the first word of the sentence
    #    and common words such as "I".
    candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text)
    for candidate in candidates:
        first = candidate.split()[0]
        if first in {"Should", "What", "Is", "Will", "Do", "Does", "How",
                     "Tell", "Give", "Check", "I", "The", "Weather"}:
            continue
        city = _clean_city(candidate)
        if city:
            return city

    return DEFAULT_CITY


def geocode_city(city: str) -> dict:
    """
    Tool 1 — Geocoding. Turns a city name into latitude/longitude
    using the free Open-Meteo Geocoding API (no API key).
    Returns {"name", "country", "admin1", "latitude", "longitude"}.
    Raises ValueError if the city is not found, RuntimeError on API errors.
    """
    try:
        resp = requests.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not reach the Open-Meteo Geocoding API for '{city}'. "
            f"Check your internet connection. ({exc})"
        ) from exc

    data = resp.json()
    results = data.get("results") or []
    if not results:
        raise ValueError(
            f"Could not find a place called '{city}'. "
            "Check the spelling and try again."
        )
    top = results[0]
    return {
        "name": top.get("name", city),
        "country": top.get("country", ""),
        "admin1": top.get("admin1", ""),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
    }


def get_weather(city: str) -> dict:
    """
    Tool 2 — Forecast. Geocodes the city, then calls the free
    Open-Meteo Forecast API for current weather + hourly precipitation
    probability. Returns real, observed numbers — never invented data.

    Returned keys: city, country, admin1, latitude, longitude,
    temperature_c, temperature_f, condition, weather_code,
    precipitation_mm, precipitation_probability (%, max over next 12h),
    humidity, wind_speed_kmh.
    """
    place = geocode_city(city)
    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "hourly": "precipitation_probability",
                "forecast_days": 2,
                "timezone": "auto",
            },
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not reach the Open-Meteo Forecast API for '{city}'. "
            f"Check your internet connection. ({exc})"
        ) from exc

    data = resp.json()
    current = data.get("current") or {}
    if "temperature_2m" not in current:
        raise RuntimeError(
            "The Forecast API returned an unexpected response "
            "(no current temperature). Please try again."
        )

    temp_c = float(current["temperature_2m"])
    code = int(current.get("weather_code", 0))

    # Precipitation probability: highest value over the next 12 hours.
    # This is the number the umbrella advice is based on.
    precip_prob = 0
    hourly = data.get("hourly") or {}
    probs = hourly.get("precipitation_probability") or []
    times = hourly.get("time") or []
    current_time = current.get("time", "")
    if probs and times and current_time:
        try:
            start = times.index(current_time)
        except ValueError:
            start = 0
        window = [p for p in probs[start:start + 12] if p is not None]
        if window:
            precip_prob = int(max(window))
    elif probs:
        window = [p for p in probs[:12] if p is not None]
        if window:
            precip_prob = int(max(window))

    return {
        "city": place["name"],
        "country": place["country"],
        "admin1": place["admin1"],
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "temperature_c": round(temp_c, 1),
        "temperature_f": round(temp_c * 9 / 5 + 32, 1),
        "condition": _WEATHER_CODES.get(code, f"Weather code {code}"),
        "weather_code": code,
        "precipitation_mm": float(current.get("precipitation", 0) or 0),
        "precipitation_probability": precip_prob,
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
    }


def create_advice(question: str, weather: dict) -> str:
    """
    Decide practical advice from the OBSERVED weather numbers.
    No weather is ever invented here — every branch reads a real value
    from the `weather` dict returned by get_weather().
    """
    temp_c = weather["temperature_c"]
    prob = weather["precipitation_probability"]
    code = weather["weather_code"]
    wind = weather.get("wind_speed_kmh") or 0
    condition = weather["condition"]

    parts: list[str] = []

    # --- Umbrella / rain decision -------------------------------------
    is_rainy = code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                        80, 81, 82, 95, 96, 99}
    is_snowy = code in {71, 73, 75, 77, 85, 86}
    mentions_umbrella = "umbrella" in question.lower()

    if is_rainy or prob >= 50:
        parts.append(
            f"Yes — carry an umbrella. {condition} with a {prob}% chance "
            "of precipitation in the next 12 hours."
        )
    elif mentions_umbrella and prob >= 20:
        parts.append(
            f"Take an umbrella just in case — {prob}% chance of "
            f"precipitation ({condition.lower()})."
        )
    elif mentions_umbrella:
        parts.append(
            f"No umbrella needed — only a {prob}% chance of precipitation "
            f"and {condition.lower()}."
        )
    elif prob >= 20:
        parts.append(
            f"There is a {prob}% chance of precipitation — "
            "keep an umbrella handy."
        )

    # --- Temperature / clothing ---------------------------------------
    if is_snowy:
        parts.append(
            "Snow is expected — wear warm, waterproof layers and "
            "waterproof shoes."
        )
    elif temp_c < 0:
        parts.append(
            f"It is {temp_c}°C — very cold. Wear a heavy winter coat, "
            "gloves and a hat."
        )
    elif temp_c < 10:
        parts.append(
            f"It is {temp_c}°C — cold. Wear a jacket or coat."
        )
    elif temp_c < 18:
        parts.append(
            f"It is {temp_c}°C — cool. A light jacket will be comfortable."
        )
    elif temp_c > 32:
        parts.append(
            f"It is {temp_c}°C — hot. Wear light clothes, stay hydrated "
            "and use sunscreen."
        )
    elif temp_c > 27:
        parts.append(
            f"It is {temp_c}°C — warm. Light clothes are fine."
        )

    # --- Wind ----------------------------------------------------------
    if wind and wind >= 40:
        parts.append(f"It is windy ({wind} km/h) — secure loose items.")
    elif wind and wind >= 25:
        parts.append(f"A bit breezy ({wind} km/h).")

    if not parts:
        parts.append(
            f"Conditions look fine — {condition.lower()}, {temp_c}°C, "
            f"{prob}% chance of precipitation."
        )

    return " ".join(parts)


def weather_agent(question: str) -> dict:
    """
    The full agent loop: GOAL -> DECIDE -> USE TOOL -> OBSERVE -> ANSWER.

    GOAL:    answer the user's weather question.
    DECIDE:  the agent cannot know live weather, so it must call a tool.
    USE TOOL: extract_city() -> geocode -> get_weather() (Forecast API).
    OBSERVE: read the real temperature / condition / precipitation chance.
    ANSWER:  create_advice() turns those numbers into practical advice.

    Returns a dict with city, temperature, condition, precipitation
    chance and advice (plus the loop steps, for transparency).
    Raises ValueError (unknown city) or RuntimeError (API unreachable).
    """
    steps = [
        f"GOAL: answer {question!r}",
        "DECIDE: live weather is needed — call a tool, do not guess",
    ]

    city = extract_city(question)
    steps.append(f"EXTRACT CITY: {city!r}")

    weather = get_weather(city)
    steps.append(
        "USE TOOL: Open-Meteo Geocoding + Forecast APIs "
        f"-> {weather['city']}, {weather['temperature_c']}°C, "
        f"{weather['condition']}, {weather['precipitation_probability']}% rain chance"
    )
    steps.append("OBSERVE: real numbers received, no weather invented")

    advice = create_advice(question, weather)
    steps.append("ANSWER: advice written from the observed numbers")

    return {
        "question": question,
        "city": weather["city"],
        "country": weather["country"],
        "admin1": weather["admin1"],
        "latitude": weather["latitude"],
        "longitude": weather["longitude"],
        "temperature_c": weather["temperature_c"],
        "temperature_f": weather["temperature_f"],
        "condition": weather["condition"],
        "weather_code": weather["weather_code"],
        "precipitation_mm": weather["precipitation_mm"],
        "precipitation_probability": weather["precipitation_probability"],
        "humidity": weather["humidity"],
        "wind_speed_kmh": weather["wind_speed_kmh"],
        "advice": advice,
        "steps": steps,
    }


# ----------------------------------------------------------------------
# OPTIONAL LLM HOOK — not used by weather_agent() and not required.
# If you later want an LLM to rephrase the advice, wire it in here
# (e.g. pass your own API key via an environment variable) and call
# it from main.py. The agent works fully without it.
# ----------------------------------------------------------------------
def ask_llm_to_rephrase_advice(advice: str) -> str | None:
    """Optional: rephrase advice with an LLM. Returns None (not wired in)."""
    return None
