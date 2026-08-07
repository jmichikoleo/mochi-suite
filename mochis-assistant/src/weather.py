"""Weather data for Busan with outfit/reminder suggestions."""

import requests
from datetime import datetime


# Weather condition -> reminder mapping
WEATHER_REMINDERS = {
    "Rain": {"icon": "🌧️", "reminder": "Bring an umbrella today!", "tip": "Roads might be slippery."},
    "Drizzle": {"icon": "🌦️", "reminder": "Light rain expected — bring an umbrella just in case.", "tip": ""},
    "Thunderstorm": {"icon": "⛈️", "reminder": "Thunderstorms expected! Stay indoors if possible.", "tip": "Avoid open areas."},
    "Snow": {"icon": "🌨️", "reminder": "Snow today! Dress warmly and wear boots.", "tip": "Leave extra time for commuting."},
    "Clouds": {"icon": "☁️", "reminder": "", "tip": "Overcast but dry."},
    "Clear": {"icon": "☀️", "reminder": "", "tip": "Beautiful day!"},
    "Mist": {"icon": "🌫️", "reminder": "Misty — be careful if driving.", "tip": "Visibility may be low."},
    "Fog": {"icon": "🌫️", "reminder": "Foggy — leave extra time for travel.", "tip": "Drive carefully."},
    "Haze": {"icon": "🌫️", "reminder": "Hazy — consider wearing a mask outdoors.", "tip": "Air quality may be poor."},
}


def fetch_weather(api_key: str, city: str = "Busan", country: str = "KR") -> dict:
    """Fetch current weather and forecast from OpenWeatherMap."""
    if not api_key or api_key == "YOUR_OPENWEATHER_API_KEY_HERE":
        return {"has_data": False, "error": "Set your OpenWeatherMap API key in config/settings.yaml"}

    try:
        # Current weather
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return {"has_data": False, "error": f"API error: {r.status_code}"}

        data = r.json()
        current = {
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data["wind"]["speed"] * 3.6, 1),  # m/s to km/h
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
        }

        # Forecast (next 12 hours in 3h intervals)
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city},{country}&appid={api_key}&units=metric&cnt=4"
        fr = requests.get(forecast_url, timeout=8)
        forecast = []
        if fr.status_code == 200:
            for item in fr.json().get("list", []):
                forecast.append({
                    "time": datetime.fromtimestamp(item["dt"]).strftime("%H:%M"),
                    "temp": round(item["main"]["temp"]),
                    "condition": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                })

        # Generate reminders
        reminders = _generate_reminders(current, forecast)

        return {
            "has_data": True,
            "city": city,
            "current": current,
            "forecast": forecast,
            "reminders": reminders,
        }
    except Exception as e:
        return {"has_data": False, "error": str(e)}


def _generate_reminders(current: dict, forecast: list) -> list:
    """Generate weather-based reminders."""
    reminders = []
    condition = current.get("condition", "")
    temp = current.get("temp", 20)
    wind = current.get("wind_speed", 0)
    feels_like = current.get("feels_like", temp)

    # Rain/weather condition reminders
    wr = WEATHER_REMINDERS.get(condition)
    if wr and wr["reminder"]:
        reminders.append({"type": "weather", "icon": wr["icon"], "text": wr["reminder"]})

    # Check forecast for upcoming rain
    if condition not in ("Rain", "Drizzle", "Thunderstorm"):
        for f in forecast:
            if f["condition"] in ("Rain", "Drizzle", "Thunderstorm"):
                reminders.append({
                    "type": "forecast",
                    "icon": "🌧️",
                    "text": f"Rain expected around {f['time']} — bring an umbrella!"
                })
                break

    # Temperature-based
    if temp <= 5:
        reminders.append({"type": "cold", "icon": "🧥", "text": f"Very cold ({temp}°C)! Wear a heavy coat, scarf, and gloves."})
    elif temp <= 12:
        reminders.append({"type": "cold", "icon": "🧥", "text": f"Chilly ({temp}°C). Bring a warm jacket."})
    elif temp >= 33:
        reminders.append({"type": "hot", "icon": "🥵", "text": f"Very hot ({temp}°C)! Stay hydrated and wear sunscreen."})
    elif temp >= 28:
        reminders.append({"type": "hot", "icon": "☀️", "text": f"Warm day ({temp}°C). Light clothes and stay hydrated."})

    # Wind
    if wind >= 40:
        reminders.append({"type": "wind", "icon": "💨", "text": f"Strong winds ({wind} km/h)! Secure loose items and be careful outside."})
    elif wind >= 25:
        reminders.append({"type": "wind", "icon": "🌬️", "text": f"Windy ({wind} km/h). Bring a windbreaker."})

    # Feels like vs actual
    if abs(feels_like - temp) >= 5:
        reminders.append({"type": "feelslike", "icon": "🌡️", "text": f"Feels like {feels_like}°C (actual {temp}°C). Dress for how it feels!"})

    if not reminders:
        wr = WEATHER_REMINDERS.get(condition, {"icon": "🌤️"})
        reminders.append({"type": "general", "icon": wr["icon"], "text": f"Nice weather ({temp}°C). Enjoy your day!"})

    return reminders
