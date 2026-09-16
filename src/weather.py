"""Current weather and three-day forecast from Open-Meteo."""

import httpx
from livekit.agents import function_tool


@function_tool
async def get_weather(location: str) -> dict:
    """Get current weather and a three-day forecast for a named city.

    Ask for a city if missing. Report the matched place and source; never guess
    the user's location. Temperatures are Celsius, wind speed is km/h.

    Args:
        location: City name, optionally including the country.
    """
    if not location.strip() or len(location) > 150:
        return {"status": "invalid_location", "message": "Bitte einen Ort nennen."}
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location.strip(), "count": 3, "language": "de"},
            )
            response.raise_for_status()
            places = response.json().get("results", [])
            if not places:
                return {
                    "status": "not_found",
                    "message": "Ort nicht gefunden. Bitte präzisieren.",
                }
            place = places[0]
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
                    "timezone": "auto",
                    "forecast_days": 3,
                },
            )
            response.raise_for_status()
            return {
                "status": "ok",
                "place": place["name"],
                "country": place.get("country"),
                "alternatives": [
                    p["name"] + ", " + p.get("country", "") for p in places[1:]
                ],
                "source": "Open-Meteo",
                "source_url": "https://open-meteo.com/",
                "weather": response.json(),
            }
    except (httpx.HTTPError, ValueError, KeyError):
        return {
            "status": "unavailable",
            "message": "Wetterdaten sind gerade nicht verfügbar.",
        }
