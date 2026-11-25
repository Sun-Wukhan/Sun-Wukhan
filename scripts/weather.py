#!/usr/bin/env python3
"""Fetch current Toronto weather from Open-Meteo and render assets/weather.svg.

Standard library only. Run by the Toronto Weather GitHub Actions workflow
(hourly) and manually whenever a fresh card is wanted.
"""

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=43.6532&longitude=-79.3832"
    "&current=temperature_2m,weather_code,is_day"
    "&timezone=America%2FToronto"
)

# WMO weather codes (Open-Meteo) -> plain labels
CONDITIONS = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Rain",
    63: "Rain",
    65: "Rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Snow",
    73: "Snow",
    75: "Snow",
    77: "Snow",
    80: "Rain showers",
    81: "Rain showers",
    82: "Rain showers",
    85: "Snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "weather.svg"


def fetch_current():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "profile-weather-card"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["current"]


def render_svg(temp_c, condition, updated_line, is_day):
    dot = "#e0af68" if is_day else "#7aa2f7"
    temp = f"{temp_c:.0f}°C"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="120" viewBox="0 0 480 120">
  <rect width="480" height="120" rx="10" fill="#1a1b27"/>
  <rect width="480" height="120" rx="10" fill="none" stroke="#414868" stroke-width="1.5"/>
  <circle cx="42" cy="46" r="13" fill="{dot}"/>
  <text x="66" y="42" font-family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif" font-size="15" fill="#7dcfff" letter-spacing="2">TORONTO, RIGHT NOW</text>
  <text x="66" y="82" font-family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif" font-size="30" font-weight="700" fill="#c0caf5">{escape(temp)} <tspan font-size="19" font-weight="400" fill="#a9b1d6">{escape(condition)}</tspan></text>
  <text x="468" y="104" text-anchor="end" font-family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif" font-size="12.5" fill="#697098">{escape(updated_line)}</text>
</svg>
"""
    return svg


def main():
    current = fetch_current()
    temp = float(current["temperature_2m"])
    code = int(current["weather_code"])
    is_day = int(current.get("is_day", 1)) == 1
    condition = CONDITIONS.get(code, "Unknown")
    # current.time is Toronto local time in ISO format, e.g. 2026-11-24T17:15
    local = datetime.fromisoformat(current["time"])
    updated = "Updated " + local.strftime("%b %-d, %-I:%M %p") + " Toronto"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_svg(temp, condition, updated, is_day), encoding="utf-8")
    print(f"Wrote {OUT}: {temp:.0f}°C, {condition}, {updated}")


if __name__ == "__main__":
    main()
