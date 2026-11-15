"""
Weather Assistant Agent — CLI entry point.

Usage:
    python main.py "Should I carry an umbrella in Delhi?"
    python main.py "What's the weather in Hartford tomorrow?"
    python main.py            # interactive mode — ask questions until you type quit
"""

from __future__ import annotations

import sys

from agent import weather_agent


def print_result(result: dict) -> None:
    """Print one agent answer in a clear, readable format."""
    location = result["city"]
    if result.get("admin1"):
        location += f", {result['admin1']}"
    if result.get("country"):
        location += f", {result['country']}"

    print()
    print(f"📍 {location}")
    print(
        f"🌡️  {result['temperature_c']}°C / {result['temperature_f']}°F"
        f"  •  {result['condition']}"
    )
    print(f"🌧️  Precipitation chance (next 12h): {result['precipitation_probability']}%")
    if result.get("precipitation_mm"):
        print(f"     Current precipitation: {result['precipitation_mm']} mm")
    if result.get("humidity") is not None:
        print(f"💧 Humidity: {result['humidity']}%", end="")
    if result.get("wind_speed_kmh") is not None:
        print(f"  •  💨 Wind: {result['wind_speed_kmh']} km/h", end="")
    if result.get("humidity") is not None or result.get("wind_speed_kmh") is not None:
        print()
    print()
    print(f"💡 Advice: {result['advice']}")
    print()
    print("Agent loop:")
    for step in result["steps"]:
        print(f"  • {step}")
    print()


def ask(question: str) -> None:
    try:
        result = weather_agent(question)
    except ValueError as exc:
        # Unknown city — a clear, user-facing message, not a traceback.
        print(f"\n❌ {exc}\n")
        return
    except RuntimeError as exc:
        # API unreachable / unexpected response.
        print(f"\n❌ {exc}\n")
        return
    print_result(result)


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        ask(" ".join(argv[1:]))
        return 0

    print("🌦️  Weather Assistant Agent — ask about the weather, or type 'quit'.")
    print("    Example: Should I carry an umbrella in Delhi?")
    print("    (No city? I will use Hartford, CT.)")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! 👋")
            return 0
        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye! 👋")
            return 0
        if not question:
            continue
        ask(question)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
