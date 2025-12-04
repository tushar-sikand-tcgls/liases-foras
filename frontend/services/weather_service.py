"""
Weather Service Module
Fetches real-time weather and air quality data for location context
"""

import requests
import os
from datetime import datetime
from typing import Dict, Optional


class WeatherService:
    """Service for fetching weather and air quality data"""

    def __init__(self):
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.google_aqi_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def get_weather_data(self, city: str, region: str) -> Dict:
        """
        Fetch weather data from OpenWeather API

        Args:
            city: City name (e.g., "Pune")
            region: Region/micromarket (e.g., "Chakan")

        Returns:
            Dict with temperature, humidity, elevation, sunrise, sunset, current_time
        """
        if not self.openweather_api_key:
            return self._get_mock_weather_data()

        try:
            # Use OpenWeather API to get coordinates first
            geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct"
            params = {
                "q": f"{region}, {city}, IN",
                "limit": 1,
                "appid": self.openweather_api_key
            }

            response = requests.get(geocoding_url, params=params, timeout=5)

            if response.status_code != 200 or not response.json():
                return self._get_mock_weather_data()

            location = response.json()[0]
            lat, lon = location['lat'], location['lon']

            # Get current weather data
            weather_url = "https://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                "lat": lat,
                "lon": lon,
                "appid": self.openweather_api_key,
                "units": "metric"  # Celsius
            }

            weather_response = requests.get(weather_url, params=weather_params, timeout=5)

            if weather_response.status_code != 200:
                return self._get_mock_weather_data()

            weather_data = weather_response.json()

            return {
                "temperature": round(weather_data['main']['temp']),
                "humidity": weather_data['main']['humidity'],
                "elevation": weather_data.get('altitude', 600),  # Default if not available
                "sunrise": weather_data['sys']['sunrise'],  # Unix timestamp
                "sunset": weather_data['sys']['sunset'],    # Unix timestamp
                "current_time": datetime.now().timestamp(),
                "weather_description": weather_data['weather'][0]['description']
            }

        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return self._get_mock_weather_data()

    def get_aqi_data(self, city: str, region: str) -> Dict:
        """
        Fetch air quality data from Google Air Quality API

        Args:
            city: City name
            region: Region/micromarket

        Returns:
            Dict with AQI value and category
        """
        if not self.google_aqi_api_key:
            return self._get_mock_aqi_data()

        try:
            # Note: Google Air Quality API requires coordinates
            # For now, return mock data until API is fully configured
            return self._get_mock_aqi_data()

        except Exception as e:
            print(f"Error fetching AQI data: {e}")
            return self._get_mock_aqi_data()

    def get_temperature_icon(self, temperature: float, current_time: float,
                            sunrise: float, sunset: float) -> str:
        """
        Get temperature icon based on time of day and temperature

        Args:
            temperature: Temperature in Celsius
            current_time: Current time (Unix timestamp)
            sunrise: Sunrise time (Unix timestamp)
            sunset: Sunset time (Unix timestamp)

        Returns:
            Icon string for temperature display
        """
        # Check if it's nighttime (between sunset and next sunrise)
        is_night = current_time < sunrise or current_time > sunset

        if is_night:
            return "🌙"  # Moon icon for night

        # Daytime icons based on temperature
        if temperature < 5:
            return "❄️"  # Snow
        elif temperature < 15:
            return "☁️"  # Cloud
        elif temperature < 25:
            return "⛅"  # Partly cloudy
        else:
            return "☀️"  # Sun

    def get_aqi_category(self, aqi_value: int) -> tuple:
        """
        Get AQI category and icon

        Args:
            aqi_value: AQI value

        Returns:
            Tuple of (icon, category_name)
        """
        if aqi_value < 50:
            return ("🟢", "Good")
        elif aqi_value < 100:
            return ("🟡", "Moderate")
        elif aqi_value < 150:
            return ("🟠", "Unhealthy (Sensitive)")
        elif aqi_value < 200:
            return ("🔴", "Unhealthy")
        elif aqi_value < 300:
            return ("🟣", "Very Unhealthy")
        else:
            return ("🟤", "Hazardous")

    def get_humidity_icon(self, humidity: int) -> str:
        """Get humidity icon based on value"""
        if humidity < 30:
            return "💧"  # Low
        elif humidity < 60:
            return "💧💧"  # Medium
        else:
            return "💧💧💧"  # High

    def _get_mock_weather_data(self) -> Dict:
        """Return mock weather data when API is unavailable"""
        current_time = datetime.now()

        # Mock sunrise at 6 AM, sunset at 6 PM
        sunrise_time = current_time.replace(hour=6, minute=0, second=0)
        sunset_time = current_time.replace(hour=18, minute=0, second=0)

        return {
            "temperature": 28,
            "humidity": 65,
            "elevation": 600,
            "sunrise": sunrise_time.timestamp(),
            "sunset": sunset_time.timestamp(),
            "current_time": current_time.timestamp(),
            "weather_description": "partly cloudy"
        }

    def _get_mock_aqi_data(self) -> Dict:
        """Return mock AQI data when API is unavailable"""
        return {
            "aqi": 156,
            "category": "Moderate"
        }
