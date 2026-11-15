"""
Tests for the Weather Assistant Agent.
Run:  python3 -m pytest test_agent.py -v
  or: python3 -m unittest test_agent -v

The live-API test skips gracefully when there is no internet.
"""
import unittest

from agent import create_advice, extract_city, get_weather, weather_agent


def fake_weather(**overrides):
    """Fake observed weather — used to test advice logic without the API."""
    weather = {
        "city": "Test City",
        "temperature_c": 20.0,
        "temperature_f": 68.0,
        "condition": "Clear sky",
        "weather_code": 0,
        "precipitation_mm": 0.0,
        "precipitation_probability": 0,
        "humidity": 50,
        "wind_speed_kmh": 10,
    }
    weather.update(overrides)
    return weather


class TestExtractCity(unittest.TestCase):
    def test_delhi(self):
        self.assertEqual(
            extract_city("Should I carry an umbrella in Delhi?"), "Delhi"
        )

    def test_new_york_multi_word(self):
        self.assertEqual(
            extract_city("What's the weather in New York tomorrow?"),
            "New York",
        )

    def test_los_angeles_multi_word(self):
        self.assertEqual(
            extract_city("Is it raining in Los Angeles today?"),
            "Los Angeles",
        )

    def test_lowercase_city(self):
        self.assertEqual(
            extract_city("should i carry an umbrella in delhi"), "Delhi"
        )

    def test_no_city_defaults_to_hartford(self):
        self.assertEqual(extract_city("Is it cold today?"), "Hartford")
        self.assertEqual(extract_city(""), "Hartford")

    def test_tomorrow_is_not_part_of_city(self):
        self.assertEqual(
            extract_city("What's the weather in Hartford tomorrow?"),
            "Hartford",
        )


class TestAdviceLogic(unittest.TestCase):
    def test_rain_means_umbrella(self):
        advice = create_advice(
            "Should I carry an umbrella?",
            fake_weather(
                weather_code=63, condition="Moderate rain",
                precipitation_probability=80, temperature_c=22.0,
            ),
        )
        self.assertIn("umbrella", advice.lower())

    def test_high_rain_chance_means_umbrella(self):
        advice = create_advice(
            "Should I carry an umbrella in Delhi?",
            fake_weather(
                weather_code=2, condition="Partly cloudy",
                precipitation_probability=70, temperature_c=25.0,
            ),
        )
        self.assertIn("umbrella", advice.lower())

    def test_no_rain_means_no_umbrella(self):
        advice = create_advice(
            "Should I carry an umbrella?",
            fake_weather(
                weather_code=0, condition="Clear sky",
                precipitation_probability=0, temperature_c=22.0,
            ),
        )
        self.assertIn("no umbrella", advice.lower())

    def test_cold_means_jacket(self):
        advice = create_advice(
            "What's the weather?",
            fake_weather(
                weather_code=0, condition="Clear sky",
                precipitation_probability=0, temperature_c=5.0,
            ),
        )
        self.assertIn("jacket", advice.lower())

    def test_hot_weather_advice(self):
        advice = create_advice(
            "What's the weather?",
            fake_weather(
                weather_code=0, condition="Clear sky",
                precipitation_probability=0, temperature_c=35.0,
            ),
        )
        self.assertIn("hot", advice.lower())


class TestLiveApi(unittest.TestCase):
    def test_live_api_smoke(self):
        """Real call to Open-Meteo. Skips gracefully with no internet."""
        try:
            weather = get_weather("Delhi")
        except (RuntimeError, ValueError) as exc:
            self.skipTest(f"Live API unavailable: {exc}")
        self.assertEqual(weather["city"], "Delhi")
        self.assertIn("temperature_c", weather)
        self.assertIn("condition", weather)
        self.assertIn("precipitation_probability", weather)
        self.assertGreaterEqual(weather["precipitation_probability"], 0)
        self.assertLessEqual(weather["precipitation_probability"], 100)

    def test_live_agent_end_to_end(self):
        """Full loop with a real question. Skips gracefully offline."""
        try:
            result = weather_agent("Should I carry an umbrella in Delhi?")
        except (RuntimeError, ValueError) as exc:
            self.skipTest(f"Live API unavailable: {exc}")
        self.assertEqual(result["city"], "Delhi")
        self.assertIn("advice", result)
        self.assertTrue(result["advice"])
        self.assertEqual(len(result["steps"]), 6)


if __name__ == "__main__":
    unittest.main()
