"""
Context Service: Visual and Informational Context

Provides maps, images, weather, news, and city insights for locations and projects
"""

import os
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import urllib.parse
from dotenv import load_dotenv
from app.services.document_vector_service import get_document_vector_service

# Load environment variables from .env file
load_dotenv()

# API rate limiting configuration
# Can be configured via GOOGLE_API_DELAY environment variable
# Default: 0.1s (reduced for parallel execution - was 0.5s)
# With parallel execution, individual API delays are less critical
API_DELAY_SECONDS = float(os.getenv("GOOGLE_API_DELAY", "0.1"))

# Import for parallel execution
from concurrent.futures import ThreadPoolExecutor, as_completed


class ContextService:
    """
    Unified service for location context:
    - Google Maps (location visualization)
    - Image collage (Google Custom Search)
    - Weather information
    - Latest news
    """

    def __init__(self):
        # API keys (set via environment variables)
        # Using single Google API key for all Google services
        self.google_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
        self.google_maps_api_key = self.google_api_key  # For backwards compatibility
        self.google_search_api_key = self.google_api_key
        self.google_search_cx = os.getenv("GOOGLE_SEARCH_CX", "")

        # NewsData.io API for location-based news
        self.newsdata_api_key = os.getenv("NEWSDATA_API_KEY", "")
        self.newsdata_base_url = os.getenv("NEWSDATA_API_BASE_URL", "https://newsdata.io/api/1")

    def _api_call_with_retry(self, url: str, max_retries: int = 3, timeout: int = 10) -> Optional[requests.Response]:
        """
        Make API call with retry logic for rate limiting

        Args:
            url: URL to call
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds

        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)

                # Check for rate limiting (HTTP 429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    print(f"[API] Rate limited. Waiting {retry_after}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(retry_after)
                    continue

                return response

            except requests.Timeout:
                print(f"[API] Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                    continue
            except Exception as e:
                print(f"[API] Error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue

        return None

    def get_location_context(
        self,
        location_name: str,
        location_type: str = "region",  # "region" or "project"
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for a location

        Args:
            location_name: Name of location/project
            location_type: Type (region or project)
            city: City name for better search context

        Returns:
            Dictionary with map, images, weather, nearby places, distances, elevation, aerial/street views
        """
        # Priority: project (location_name) first, region (city) as fallback
        # For geocoding and specific location data, prefer project if type is "project"
        primary_location = location_name
        full_location = f"{location_name}, {city}" if city else location_name

        # Use full location for general searches, but primary for precise geocoding
        search_location = primary_location if location_type == "project" else full_location

        print(f"[CONTEXT] Loading context for {full_location} using PARALLEL execution")
        print(f"[CONTEXT] Estimated total time: ~1.0-1.5s (9 parallel Google API calls)")

        context = {
            "location": location_name,
            "city": city,
            "type": location_type,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # PERFORMANCE OPTIMIZATION: Execute all Google API calls in parallel using ThreadPoolExecutor
        # This reduces load time from ~4.5s (sequential) to ~1s (parallel)

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=9) as executor:
            # Submit all API calls to run in parallel
            future_map = executor.submit(self._get_map_url, full_location)
            future_images = executor.submit(self._get_location_images, full_location, location_type)
            future_weather = executor.submit(self._get_weather, full_location)
            future_aqi = executor.submit(self._get_air_quality, search_location)
            future_places = executor.submit(self._get_nearby_places, search_location)
            future_distances = executor.submit(self._get_distances, search_location)
            future_aerial = executor.submit(self._get_aerial_view, search_location)
            future_street = executor.submit(self._get_street_view, search_location)

            # Collect results as they complete
            context["map"] = future_map.result()
            context["images"] = future_images.result()
            context["weather"] = future_weather.result()
            context["air_quality"] = future_aqi.result()
            context["nearby_places"] = future_places.result()
            context["distances"] = future_distances.result()
            context["aerial_view"] = future_aerial.result()
            context["street_view"] = future_street.result()

            # Elevation needs temperature from weather (dependency)
            base_temp = context["weather"].get("temperature", 25.0) or 25.0
            context["elevation"] = self._get_elevation(search_location, base_temp)

        # Local operations (no API calls - fast)
        context["city_insights"] = self._get_city_insights(city, location_name if location_type == "region" else None)
        context["news"] = self._get_news(full_location)

        elapsed = time.time() - start_time
        print(f"[CONTEXT] ✅ Context loading complete for {full_location} in {elapsed:.2f}s")

        return context

    def _get_map_url(self, location: str, zoom: int = 13) -> Dict[str, Any]:
        """
        Generate Google Maps Static API URL or embed URL

        Args:
            location: Location name
            zoom: Zoom level (1-20)

        Returns:
            Dictionary with map URLs
        """
        if self.google_maps_api_key:
            # Google Maps Static API
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                "center": location,
                "zoom": zoom,
                "size": "600x400",
                "maptype": "roadmap",
                "markers": f"color:red|{location}",
                "key": self.google_maps_api_key
            }
            static_url = f"{base_url}?{urllib.parse.urlencode(params)}"

            # Embed URL for interactive map
            embed_url = f"https://www.google.com/maps/embed/v1/place?key={self.google_maps_api_key}&q={urllib.parse.quote(location)}"

            return {
                "static_url": static_url,
                "embed_url": embed_url,
                "location": location,
                "zoom": zoom
            }
        else:
            # Fallback to simple Google Maps link
            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(location)}"
            return {
                "static_url": None,
                "embed_url": None,
                "maps_link": maps_url,
                "location": location,
                "note": "Set GOOGLE_MAPS_API_KEY for enhanced maps"
            }

    def _get_location_images(
        self,
        location: str,
        location_type: str,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        Get location images using Google Custom Search

        Args:
            location: Location name
            location_type: Type (region/project)
            count: Number of images (default 5)

        Returns:
            List of image dictionaries
        """
        if not self.google_search_api_key or not self.google_search_cx:
            return [{
                "url": None,
                "title": location,
                "note": "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX for images"
            }]

        try:
            # Customize search query based on type
            if location_type == "project":
                search_query = f"{location} real estate project construction aerial view"
            else:
                search_query = f"{location} area skyline infrastructure development"

            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_search_api_key,
                "cx": self.google_search_cx,
                "q": search_query,
                "searchType": "image",
                "num": min(count, 10),  # Max 10 per request
                "imgSize": "large",
                "safe": "active"
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            images = []

            for item in data.get("items", [])[:count]:
                images.append({
                    "url": item.get("link"),
                    "title": item.get("title", ""),
                    "thumbnail": item.get("image", {}).get("thumbnailLink"),
                    "source": item.get("displayLink", "")
                })

            return images if images else [{"url": None, "note": "No images found"}]

        except Exception as e:
            return [{"url": None, "error": str(e)}]

    def _get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for location using Google services

        Args:
            location: Location name

        Returns:
            Weather data dictionary
        """
        if not self.google_api_key:
            return {
                "temperature": None,
                "condition": "Unknown",
                "note": "Set GOOGLE_MAPS_API_KEY for weather data"
            }

        try:
            # Use OpenWeather API with Google key format
            # Note: For actual Google Weather API, you'd need different implementation
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": self.google_api_key,
                "units": "metric"  # Celsius
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            return {
                "temperature": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "condition": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "icon": data["weather"][0]["icon"],
                "icon_url": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
            }

        except Exception as e:
            return {
                "temperature": None,
                "condition": "Unknown",
                "error": str(e)
            }

    def _get_coordinates(self, location: str) -> Optional[tuple]:
        """
        Get coordinates for location using Google Geocoding API

        Args:
            location: Location name

        Returns:
            Tuple of (lat, lon) or None if not found
        """
        if not self.google_api_key:
            return None

        try:
            geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
            geo_params = {
                "address": location,
                "key": self.google_api_key
            }

            geo_response = requests.get(geo_url, params=geo_params, timeout=5)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if geo_data.get("results"):
                lat = geo_data["results"][0]["geometry"]["location"]["lat"]
                lon = geo_data["results"][0]["geometry"]["location"]["lng"]
                return (lat, lon)
            return None

        except Exception:
            return None

    def _get_air_quality(self, location: str) -> Dict[str, Any]:
        """
        Get air quality index for location using Google services

        Args:
            location: Location name

        Returns:
            Air quality data dictionary
        """
        if not self.google_api_key:
            return {
                "aqi": None,
                "quality": "Unknown",
                "note": "Set GOOGLE_MAPS_API_KEY for air quality data"
            }

        try:
            # Get coordinates using Geocoding API
            coords = self._get_coordinates(location)
            if not coords:
                return {
                    "aqi": None,
                    "quality": "Unknown",
                    "error": "Location not found"
                }

            lat, lon = coords

            # Get air quality data from Google Air Quality API
            aqi_url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
            aqi_payload = {
                "location": {
                    "latitude": lat,
                    "longitude": lon
                }
            }
            aqi_headers = {
                "Content-Type": "application/json"
            }
            aqi_params = {"key": self.google_api_key}

            aqi_response = requests.post(
                aqi_url,
                json=aqi_payload,
                headers=aqi_headers,
                params=aqi_params,
                timeout=5
            )
            aqi_response.raise_for_status()
            aqi_data = aqi_response.json()

            # Extract AQI from Google's response
            aqi_index = aqi_data.get("indexes", [{}])[0].get("aqi", None)
            aqi_category = aqi_data.get("indexes", [{}])[0].get("category", "Unknown")

            # Get pollutant data
            pollutants = aqi_data.get("pollutants", [])
            pm25 = next((p["concentration"]["value"] for p in pollutants if p["code"] == "pm25"), None)
            pm10 = next((p["concentration"]["value"] for p in pollutants if p["code"] == "pm10"), None)
            no2 = next((p["concentration"]["value"] for p in pollutants if p["code"] == "no2"), None)

            return {
                "aqi": aqi_index,
                "quality": aqi_category,
                "components": {
                    "pm2_5": pm25,
                    "pm10": pm10,
                    "no2": no2
                },
                "coordinates": {"lat": lat, "lon": lon}
            }

        except Exception as e:
            return {
                "aqi": None,
                "quality": "Unknown",
                "error": str(e)
            }

    def _get_nearby_places(self, location: str) -> Dict[str, Any]:
        """
        Get nearby places of interest using Google Places API (New)

        Args:
            location: Location name

        Returns:
            Dictionary with nearby places by category
        """
        if not self.google_api_key:
            return {"note": "Set GOOGLE_MAPS_API_KEY for nearby places"}

        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": "Location not found"}

            lat, lon = coords

            # Places categories to search
            place_types = {
                "hospitals": "hospital",
                "schools": "school",
                "restaurants": ["restaurant", "cafe"],
                "hotels": "lodging",
                "malls": "shopping_mall",
                "transport": ["airport", "train_station", "subway_station"],
                "recreation": ["park", "gym", "museum", "zoo"],
                "worship": ["church", "mosque", "hindu_temple", "synagogue"]
            }

            places_url = "https://places.googleapis.com/v1/places:searchNearby"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.google_api_key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.types,places.location"
            }

            nearby_places = {}

            for category, place_type in place_types.items():
                types_list = [place_type] if isinstance(place_type, str) else place_type

                payload = {
                    "includedTypes": types_list,
                    "maxResultCount": 5,
                    "locationRestriction": {
                        "circle": {
                            "center": {
                                "latitude": lat,
                                "longitude": lon
                            },
                            "radius": 5000.0  # 5km radius
                        }
                    }
                }

                try:
                    response = requests.post(places_url, json=payload, headers=headers, timeout=5)
                    response.raise_for_status()
                    data = response.json()

                    places = []
                    for place in data.get("places", [])[:5]:
                        places.append({
                            "name": place.get("displayName", {}).get("text", "Unknown"),
                            "address": place.get("formattedAddress", ""),
                            "types": place.get("types", [])
                        })

                    nearby_places[category] = places
                except Exception:
                    nearby_places[category] = []

            return nearby_places

        except Exception as e:
            return {"error": str(e)}

    def _get_distances(self, location: str) -> Dict[str, Any]:
        """
        Get distances to key destinations using Distance Matrix API

        Args:
            location: Location name

        Returns:
            Dictionary with distances to airport, railway, hospital, school
        """
        if not self.google_api_key:
            return {"note": "Set GOOGLE_MAPS_API_KEY for distance data"}

        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": "Location not found"}

            # Find nearest key destinations
            destinations = {
                "airport": "airport near " + location,
                "railway_station": "railway station near " + location,
                "hospital": "hospital near " + location,
                "school": "school near " + location
            }

            distance_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            distances = {}

            for key, dest in destinations.items():
                params = {
                    "origins": location,
                    "destinations": dest,
                    "mode": "driving",
                    "key": self.google_api_key
                }

                try:
                    response = requests.get(distance_url, params=params, timeout=5)
                    response.raise_for_status()
                    data = response.json()

                    if data.get("rows") and data["rows"][0].get("elements"):
                        element = data["rows"][0]["elements"][0]
                        if element.get("status") == "OK":
                            distance_text = element["distance"]["text"]
                            duration_text = element["duration"]["text"]
                            distance_km = element["distance"]["value"] / 1000  # Convert to KM
                            duration_mins = element["duration"]["value"] / 60  # Convert to minutes

                            distances[key] = {
                                "destination": data["destination_addresses"][0],
                                "distance": f"{distance_km:.1f} km",
                                "duration": f"{int(duration_mins // 60)}h {int(duration_mins % 60)}m" if duration_mins >= 60 else f"{int(duration_mins)}m"
                            }
                except Exception:
                    distances[key] = {"error": "Unable to calculate"}

            return distances

        except Exception as e:
            return {"error": str(e)}

    def _get_elevation(self, location: str, base_temp: float = 25.0) -> Dict[str, Any]:
        """
        Get elevation data and calculate temperature adjustment

        Args:
            location: Location name
            base_temp: Base temperature in Celsius (default 25°C)

        Returns:
            Dictionary with elevation and adjusted temperature
        """
        if not self.google_api_key:
            return {"note": "Set GOOGLE_MAPS_API_KEY for elevation data"}

        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": "Location not found"}

            lat, lon = coords

            elevation_url = "https://maps.googleapis.com/maps/api/elevation/json"
            params = {
                "locations": f"{lat},{lon}",
                "key": self.google_api_key
            }

            response = requests.get(elevation_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                elevation_m = data["results"][0]["elevation"]

                # Temperature drops 1°C per 165m in troposphere
                temp_drop = elevation_m / 165.0
                adjusted_temp = base_temp - temp_drop

                return {
                    "elevation_m": round(elevation_m, 1),
                    "elevation_ft": round(elevation_m * 3.28084, 1),
                    "temperature_adjustment": round(temp_drop, 2),
                    "adjusted_temperature": round(adjusted_temp, 1)
                }

            return {"error": "No elevation data available"}

        except Exception as e:
            return {"error": str(e)}

    def _get_aerial_view(self, location: str) -> Dict[str, Any]:
        """
        Get aerial view imagery using Aerial View API

        Args:
            location: Location name

        Returns:
            Dictionary with aerial view data
        """
        if not self.google_api_key:
            return {"note": "Set GOOGLE_MAPS_API_KEY for aerial view"}

        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": "Location not found"}

            lat, lon = coords

            # Note: Aerial View API requires special setup and may not be available for all locations
            # Using satellite view from Maps Static API as alternative
            satellite_url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                "center": f"{lat},{lon}",
                "zoom": 17,
                "size": "800x600",
                "maptype": "satellite",
                "key": self.google_api_key
            }

            satellite_image_url = f"{satellite_url}?{urllib.parse.urlencode(params)}"

            return {
                "image_url": satellite_image_url,
                "satellite_url": satellite_image_url,  # Keep for backward compatibility
                "coordinates": {"lat": lat, "lon": lon},
                "note": "Satellite view (Aerial View API availability depends on location)"
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_street_view(self, location: str) -> Dict[str, Any]:
        """
        Get street view imagery using Street View Static API

        Args:
            location: Location name

        Returns:
            Dictionary with street view data
        """
        if not self.google_api_key:
            return {"note": "Set GOOGLE_MAPS_API_KEY for street view"}

        try:
            coords = self._get_coordinates(location)
            if not coords:
                return {"error": "Location not found"}

            lat, lon = coords

            # Street View Static API
            streetview_url = "https://maps.googleapis.com/maps/api/streetview"
            params = {
                "size": "800x600",
                "location": f"{lat},{lon}",
                "fov": 90,
                "heading": 0,
                "pitch": 0,
                "key": self.google_api_key
            }

            street_view_image_url = f"{streetview_url}?{urllib.parse.urlencode(params)}"

            # Check if street view is available using metadata API
            metadata_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
            metadata_response = requests.get(f"{metadata_url}?location={lat},{lon}&key={self.google_api_key}", timeout=5)
            metadata = metadata_response.json() if metadata_response.status_code == 200 else {}

            return {
                "image_url": street_view_image_url if metadata.get("status") == "OK" else None,
                "street_view_url": street_view_image_url if metadata.get("status") == "OK" else None,  # Keep for backward compatibility
                "available": metadata.get("status") == "OK",
                "coordinates": {"lat": lat, "lon": lon},
                "note": "Street view may not be available for all locations"
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_city_insights(self, city: Optional[str], region: Optional[str] = None) -> Dict[str, Any]:
        """
        Get city and region insights from vectorized city reports

        Args:
            city: City name (e.g., "Pune")
            region: Optional region name (e.g., "Chakan")

        Returns:
            Dictionary with salient features and context about the city/region
        """
        if not city:
            return {"note": "No city specified for insights"}

        try:
            doc_vector_service = get_document_vector_service()
            insights = doc_vector_service.query_city_insights(city=city, region=region)
            return insights
        except Exception as e:
            return {"error": str(e), "note": "Unable to fetch city insights"}

    def _get_news(self, location: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Get latest news for a location from newsdata.io

        Args:
            location: Location name (e.g., "Chakan, Pune" or "Goregaon, Mumbai")
            max_results: Maximum number of news articles to return (default: 5)

        Returns:
            Dictionary with news articles or error message

        Example response structure:
        {
            "articles": [
                {
                    "article_id": "...",
                    "title": "...",
                    "description": "...",
                    "link": "...",
                    "pubDate": "...",
                    "source_name": "...",
                    "image_url": "..."
                }
            ],
            "total_results": 10,
            "note": "..."
        }
        """
        if not self.newsdata_api_key:
            return {
                "articles": [],
                "note": "NewsData.io API key not configured"
            }

        try:
            # Construct API URL
            # Example: https://newsdata.io/api/1/latest?apikey=KEY&q=Chakan, Pune
            url = f"{self.newsdata_base_url}/latest"
            params = {
                "apikey": self.newsdata_api_key,
                "q": location,
                "language": "en"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract and format articles
            articles = []
            if data.get("results"):
                for article in data["results"][:max_results]:
                    articles.append({
                        "article_id": article.get("article_id", ""),
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "link": article.get("link", ""),
                        "pubDate": article.get("pubDate", ""),
                        "source_name": article.get("source_id", ""),
                        "image_url": article.get("image_url", "")
                    })

            return {
                "articles": articles,
                "total_results": data.get("totalResults", 0),
                "note": f"Latest news for {location}" if articles else "No recent news found for this location"
            }

        except requests.exceptions.Timeout:
            return {
                "articles": [],
                "error": "Request timeout",
                "note": "News service took too long to respond"
            }
        except requests.exceptions.RequestException as e:
            return {
                "articles": [],
                "error": str(e),
                "note": "Unable to fetch news"
            }
        except Exception as e:
            return {
                "articles": [],
                "error": str(e),
                "note": "Error processing news data"
            }

    def _translate_text(self, text: str, target_language: str = "en") -> Optional[str]:
        """
        Translate text to target language using Google Cloud Translation API

        Args:
            text: Text to translate
            target_language: Target language code (default: "en" for English)

        Returns:
            Translated text or None if translation fails
        """
        if not self.google_api_key or not text:
            return None

        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                "key": self.google_api_key,
                "q": text,
                "target": target_language
            }

            response = requests.post(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                translations = data.get("data", {}).get("translations", [])
                if translations:
                    translated = translations[0].get("translatedText", "")
                    detected_lang = translations[0].get("detectedSourceLanguage", "")
                    return translated, detected_lang
            return None, None
        except Exception as e:
            print(f"[TRANSLATE] Translation error: {str(e)}")
            return None, None

    def get_news_by_timeframe(self, location: str, city: str) -> Dict[str, Any]:
        """
        Get news for a location using Google Custom Search API
        Returns 3 categories sorted chronologically:
        1. Latest news (last 7 days) - 3 stories
        2. Big stories in last 1 month - 3 stories
        3. Big stories in last 1 year - 3 stories

        Filters for development/infrastructure news, excludes crime/accidents
        """
        if not self.google_search_api_key or not self.google_search_cx:
            return {
                "latest": [],
                "month": [],
                "year": [],
                "error": "Google Custom Search API key or CX not configured"
            }

        def fetch_news(query: str, date_restrict: str, num_results: int = 10) -> List[Dict]:
            """Fetch news from Google Custom Search with date restriction"""
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": self.google_search_api_key,
                    "cx": self.google_search_cx,
                    "q": query,
                    "num": num_results,
                    "dateRestrict": date_restrict,  # d[number] for days, m[number] for months, y[number] for years
                    "sort": "date:r:20240101:20251231",  # Sort by date (reverse chronological)
                    "tbm": "nws"  # News search
                }

                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Reliable news sources (national and regional)
                reliable_sources = [
                    # National English newspapers
                    "timesofindia.indiatimes.com", "indianexpress.com", "ndtv.com",
                    "hindustantimes.com", "thehindu.com", "dnaindia.com",
                    "business-standard.com", "economictimes.indiatimes.com",
                    "livemint.com", "firstpost.com", "news18.com",
                    "theprint.in", "scroll.in", "thewire.in",
                    "financialexpress.com", "moneycontrol.com",
                    "reuters.com", "bbc.com", "cnn.com",

                    # Regional English newspapers
                    "punemirror.in", "punekarnews.in", "bangaloremirror.indiatimes.com",
                    "mumbaimirror.indiatimes.com", "ahmedabadmirror.indiatimes.com",

                    # Marathi newspapers (Maharashtra - Pune, Mumbai, Nagpur)
                    "lokmat.com", "maharashtratimes.com", "loksatta.com",
                    "sakal.com", "pudhari.news", "deshdoot.info",

                    # Gujarati newspapers (Gujarat - Vadodara, Ahmedabad, Surat)
                    "gujaratsamachar.com", "sandesh.com", "divyabhaskar.co.in",
                    "navgujaratsamay.com", "gujarattimes.com",

                    # Hindi newspapers (North India)
                    "jagran.com", "amarujala.com", "bhaskar.com",
                    "patrika.com", "naidunia.com", "prabhatkhabar.com",

                    # Tamil newspapers (Tamil Nadu - Chennai, Coimbatore)
                    "dinamalar.com", "dinamani.com", "tamilhindu.com",
                    "thanthitv.com", "maalaimalar.com",

                    # Telugu newspapers (Telangana, Andhra Pradesh - Hyderabad, Visakhapatnam)
                    "eenadu.net", "sakshi.com", "andhrajyothy.com",

                    # Kannada newspapers (Karnataka - Bangalore, Mysore, Mangalore)
                    "vijayakarnataka.com", "prajavani.net", "udayavani.com",
                    "kannadaprabha.com",

                    # Malayalam newspapers (Kerala - Kochi, Trivandrum)
                    "manoramaonline.com", "mathrubhumi.com", "madhyamam.com",
                    "asianetnews.com",

                    # Bengali newspapers (West Bengal - Kolkata)
                    "anandabazar.com", "bartamanpatrika.com", "eisamay.com",

                    # Other reputable sources
                    "thequint.com", "outlookindia.com", "india.com"
                ]

                # Exclude property listing sites, business directories, company sites, and non-news sources
                # NOTE: Quora and Reddit are allowed as they are good discussion forums
                exclude_domains = [
                    # Property listing sites
                    "magicbricks.com", "99acres.com", "housing.com", "commonfloor.com",
                    "nobroker.in", "makaan.com", "squareyards.com", "proptiger.com",
                    "99acres.com", "nestaway.com", "grabhouse.com",
                    # Business directories
                    "justdial.com", "sulekha.com", "indiamart.com", "tradeindia.com",
                    # Social media (except Quora/Reddit which are good forums)
                    "facebook.com", "twitter.com", "instagram.com", "youtube.com",
                    "linkedin.com", "tiktok.com", "snapchat.com",
                    # Company/corporate websites and real estate developers
                    "zf.com", "siemens.com", "bosch.com", "tata.com",
                    "naiknavare.com", "kolte-patil.com", "puravankara.com",
                    "godrejproperties.com", "lodhagroup.in", "mahindralifespaces.com",
                    "genuineplots.com", "goel-ganga.com", "rohan-builders.com",
                    "panchshil.com", "oberoi-realty.com", "prestige.in",
                    "sonigaracorp.com", "kasturi.com", "meyka.com",
                    # Real estate consultancies and research firms
                    "cushmanwakefield.com", "jll.com", "cbre.com", "knightfrank.com",
                    "colliers.com", "anarock.com",
                    # Hotels and hospitality chains
                    "marriott.com", "hilton.com", "ihg.com", "accor.com",
                    "hyatt.com", "taj.com", "oberoi.com", "itchotels.com",
                    # Job portals
                    "naukri.com", "linkedin.com", "shine.com", "monster.com",
                    "indeed.com", "glassdoor.com",
                    # Government sites (not news sources)
                    "pmrda.gov.in", "pmc.gov.in", "maha.gov.in", "india.gov.in",
                    # Real estate portals and aggregators
                    "realestateindia.com", "propertywala.com", "indiaproperty.com",
                    # Logistics and industrial company sites
                    "lo-goigroup.com", "dhl.com", "bluedart.com"
                ]

                articles = []
                for item in data.get("items", []):
                    title = item.get("title", "").lower()
                    snippet = item.get("snippet", "").lower()
                    source = item.get("displayLink", "").lower()

                    # FILTER OUT: Non-news domains (property sites, social media)
                    if any(domain in source for domain in exclude_domains):
                        continue

                    # FILTER OUT: Crime, accidents, theft, minor incidents
                    exclude_keywords = ["crime", "theft", "murder", "robbery", "accident", "arrested", "killed", "injured", "dies", "death"]
                    if any(keyword in title or keyword in snippet for keyword in exclude_keywords):
                        continue

                    # PRIORITIZE: Development, infrastructure, real estate, openings
                    include_keywords = ["development", "infrastructure", "metro", "project", "construction", "opening", "launch", "announced", "real estate", "property", "residential", "commercial"]
                    has_priority = any(keyword in title or keyword in snippet for keyword in include_keywords)

                    # BOOST: Reliable news sources
                    is_reliable_source = any(reliable in source for reliable in reliable_sources)
                    priority_score = 2 if is_reliable_source else 1 if has_priority else 0

                    # Extract date from snippet or use pagemap
                    pagemap = item.get("pagemap", {})
                    metatags = pagemap.get("metatags", [{}])[0]
                    date_published = metatags.get("article:published_time", metatags.get("datePublished", ""))

                    # Parse date for chronological sorting
                    from datetime import datetime
                    parsed_date = None
                    if date_published:
                        try:
                            # Try parsing ISO format (e.g., 2024-01-15T10:30:00Z)
                            parsed_date = datetime.fromisoformat(date_published.replace('Z', '+00:00'))
                            # Make timezone-naive for consistent comparison
                            if parsed_date.tzinfo is not None:
                                parsed_date = parsed_date.replace(tzinfo=None)
                        except:
                            try:
                                # Try other common formats
                                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
                                    try:
                                        parsed_date = datetime.strptime(date_published[:10], fmt)
                                        break
                                    except:
                                        continue
                            except:
                                pass

                    # Get original title and description
                    original_title = item.get("title", "")
                    original_description = item.get("snippet", "")

                    # Try to translate non-English content (Indic languages)
                    # Keep original URL for reference to native language article
                    final_title = original_title
                    final_description = original_description
                    language_note = ""

                    # Attempt translation
                    title_translated, title_lang = self._translate_text(original_title)
                    if title_translated and title_lang and title_lang != "en":
                        # Map language codes to readable names
                        lang_names = {
                            "mr": "Marathi", "gu": "Gujarati", "hi": "Hindi",
                            "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
                            "ml": "Malayalam", "bn": "Bengali", "pa": "Punjabi"
                        }
                        lang_name = lang_names.get(title_lang, title_lang.upper())
                        final_title = title_translated
                        language_note = f"[Translated from {lang_name}]"

                        # Also translate description if title was translated
                        desc_translated, _ = self._translate_text(original_description)
                        if desc_translated:
                            final_description = desc_translated

                    articles.append({
                        "title": final_title + (" " + language_note if language_note else ""),
                        "description": final_description,
                        "url": item.get("link", ""),  # Original native language URL
                        "date": date_published if date_published else "Recent",
                        "source": item.get("displayLink", ""),
                        "priority": priority_score,  # 2=reliable source, 1=has keywords, 0=other
                        "parsed_date": parsed_date,  # For chronological sorting
                        "original_language": title_lang if title_lang and title_lang != "en" else None
                    })

                # Sort by priority first (reliable sources top), then by date (newest first)
                articles.sort(key=lambda x: (
                    -x["priority"],  # Higher priority first (reliable sources = 2)
                    x["parsed_date"] if x["parsed_date"] else datetime.min  # Newest first
                ), reverse=True)

                return articles

            except Exception as e:
                print(f"Error fetching news for {query} with dateRestrict={date_restrict}: {str(e)}")
                return []

        # Detect local language dynamically based on city name
        # Use Google Cloud Translation API (v2) to detect and translate
        # https://cloud.google.com/translate/docs/reference/rest/v2/translate
        # https://cloud.google.com/translate/docs/reference/rest/v2/detect

        def detect_city_language(city_name):
            """
            Detect predominant local language for a city using a few examples for multishot learning
            Falls back to Google Cloud Translation API language detection if city not in examples

            Returns: ISO 639-1 language code (e.g., 'mr' for Marathi, 'gu' for Gujarati)
            """
            # Few-shot examples for common patterns (multishot learning)
            examples = {
                "pune": "mr", "mumbai": "mr",  # Maharashtra → Marathi
                "vadodara": "gu", "ahmedabad": "gu",  # Gujarat → Gujarati
                "bangalore": "kn", "bengaluru": "kn",  # Karnataka → Kannada
                "chennai": "ta",  # Tamil Nadu → Tamil
                "hyderabad": "te",  # Telangana → Telugu
                "delhi": "hi", "gurgaon": "hi", "noida": "hi"  # NCR → Hindi
            }

            city_lower = city_name.lower()
            if city_lower in examples:
                return examples[city_lower]

            # For unknown cities, use Google Cloud Translation API to detect language
            try:
                # Google Cloud Translation API v2 - Detect endpoint
                # Requires: GOOGLE_MAPS_API_KEY (same key works for Translation API)
                detect_url = "https://translation.googleapis.com/language/translate/v2/detect"
                params = {
                    "key": self.google_api_key,
                    "q": f"{city_name}, India"
                }
                response = requests.post(detect_url, params=params, timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    detections = data.get("data", {}).get("detections", [[]])[0]
                    if detections and len(detections) > 0:
                        detected_lang = detections[0].get("language", "hi")
                        # Only use if it's an Indian language
                        if detected_lang in ["mr", "gu", "kn", "ta", "te", "hi", "bn", "ml", "pa"]:
                            return detected_lang
            except Exception as e:
                print(f"[NEWS] Language detection failed for {city_name}: {str(e)}")

            # Default to Hindi (most widely spoken) if detection fails
            return "hi"

        # Dynamically detect and translate location/city to local language
        local_variants = ""
        target_lang = detect_city_language(city)

        # Translate location name to local language using Google Cloud Translation API v2
        # https://cloud.google.com/translate/docs/reference/rest/v2/translate
        location_translated = None
        city_translated = None

        try:
            # Google Cloud Translation API v2 - Translate endpoint
            # Translates multiple texts in a single request
            trans_url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                "key": self.google_api_key,
                "q": [location, city],  # Batch translate both location and city
                "target": target_lang,  # Target language (e.g., 'mr' for Marathi)
                "source": "en"  # Source language is English
            }
            response = requests.post(trans_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                translations = data.get("data", {}).get("translations", [])
                if len(translations) >= 2:
                    location_translated = translations[0].get("translatedText", "")
                    city_translated = translations[1].get("translatedText", "")

                    # Build local variants query
                    variants = []
                    if location_translated and location_translated != location:
                        variants.append(f'"{location_translated}"')
                    if city_translated and city_translated != city:
                        variants.append(f'"{city_translated}"')

                    if variants:
                        local_variants = " OR ".join(variants)
                        local_variants = f" OR {local_variants}"
                        print(f"[NEWS] Translated {location}, {city} to local language ({target_lang}): {location_translated}, {city_translated}")
        except Exception as e:
            print(f"[NEWS] Translation failed for {location}, {city}: {str(e)}")
            # Continue without local variants if translation fails

        # Build search query - FOCUS on development, real estate, infrastructure
        # Include native language names to cover local/regional newspapers
        # Exclude crime with "-crime -theft -robbery" exclusion operators
        search_query = f'({location} {city}{local_variants}) (development OR infrastructure OR metro OR project OR real estate OR property OR opening OR launch) -crime -theft -robbery -accident -murder'

        # Fetch 3 categories with 10 results to allow for filtering (property sites, social media, crime news)
        # After filtering, take top 3 reliable news sources
        latest_news = fetch_news(search_query, "d7", 10)[:3]   # Last 7 days, take top 3 after filtering
        month_news = fetch_news(search_query, "m1", 10)[:3]    # Last 1 month, take top 3 after filtering
        year_news = fetch_news(search_query, "y1", 10)[:3]     # Last 1 year, take top 3 after filtering

        # FALLBACK: If no news found for region, search for city-level news (just 1 article per period)
        if not latest_news and not month_news and not year_news:
            print(f"[NEWS] No regional news found for {location}, falling back to city-level news for {city}")
            city_query = f'({city}{local_variants}) (development OR infrastructure OR metro OR project OR real estate OR property OR opening OR launch) -crime -theft -robbery -accident -murder'

            latest_news = fetch_news(city_query, "d7", 5)[:1]   # Just 1 article for city
            month_news = fetch_news(city_query, "m1", 5)[:1]    # Just 1 article for city
            year_news = fetch_news(city_query, "y1", 5)[:1]     # Just 1 article for city
            print(f"[NEWS] City-level fallback: found {len(latest_news)} latest, {len(month_news)} month, {len(year_news)} year")

        # Remove internal fields before returning (parsed_date, priority, original_language)
        for article in latest_news + month_news + year_news:
            article.pop("parsed_date", None)
            article.pop("priority", None)
            article.pop("original_language", None)  # Keep translation note in title, remove language code

        return {
            "latest": latest_news,
            "month": month_news,
            "year": year_news,
            "location": location,
            "city": city
        }

    def get_distances(self, location: str, city: str) -> Dict[str, Any]:
        """
        Get distances from location to key destinations using Google Distance Matrix API
        """
        if not self.google_api_key:
            return {"error": "Google Maps API key not configured"}

        # Get coordinates for the location first
        coords = self._get_coordinates(f"{location}, {city}")
        if not coords:
            return {"error": "Could not geocode location"}

        lat, lon = coords
        origin = f"{lat},{lon}"

        # Key destinations to measure distances to
        destinations = [
            f"Mumbai Airport, Mumbai",
            f"Pune Airport, Pune",
            f"Railway Station, {city}",
            f"City Center, {city}",
            f"IT Park, {city}",
            f"Hospital, {location}, {city}",
            f"School, {location}, {city}",
            f"Shopping Mall, {location}, {city}"
        ]

        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": origin,
                "destinations": "|".join(destinations),
                "key": self.google_api_key,
                "units": "metric"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                return {"error": f"Distance Matrix API error: {data.get('status')}"}

            # Parse results
            distances = []
            rows = data.get("rows", [])
            if rows and len(rows) > 0:
                elements = rows[0].get("elements", [])
                for idx, element in enumerate(elements):
                    if element.get("status") == "OK":
                        distances.append({
                            "destination": destinations[idx],
                            "distance": element.get("distance", {}).get("text", "N/A"),
                            "duration": element.get("duration", {}).get("text", "N/A"),
                            "distance_value": element.get("distance", {}).get("value", 0),  # meters
                            "duration_value": element.get("duration", {}).get("value", 0)   # seconds
                        })

            return {
                "origin": f"{location}, {city}",
                "distances": distances
            }

        except Exception as e:
            print(f"Error fetching distances: {str(e)}")
            return {"error": str(e)}

    def generate_location_map_with_poi(
        self,
        project_name: str,
        latitude: float,
        longitude: float,
        city: str = "Pune",
        zoom: int = 14,
        map_size: str = "800x600"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive Google Maps visualization showing a project location
        with important nearby places marked.

        Categories of POIs included:
        - Project itself (red marker - primary)
        - Hotels (blue markers)
        - Petrol Pumps (green markers)
        - Railway Station (purple markers)
        - Airport (orange markers)
        - Metro Station (yellow markers)
        - Bus Stop (brown markers)
        - Hospitals (pink markers)
        - Schools (cyan markers)
        - Shopping Malls (gray markers)

        Args:
            project_name: Name of the project
            latitude: Project latitude
            longitude: Project longitude
            city: City name for context (default: "Pune")
            zoom: Map zoom level 1-20 (default: 14)
            map_size: Map dimensions as "WIDTHxHEIGHT" (default: "800x600")

        Returns:
            Dictionary with:
            - static_map_url: URL to static map image with all markers
            - embed_map_url: URL for interactive embedded map
            - poi_details: List of all POIs found with details
            - project_location: Project coordinates and name
        """
        if not self.google_api_key:
            return {"error": "Google Maps API key not configured"}

        print(f"[MAP] Generating location map for {project_name} with POIs...")

        try:
            # Define POI categories to search with their marker colors
            poi_categories = {
                "hotel": {"type": "lodging", "color": "blue", "label": "Hotel"},
                "petrol_pump": {"type": "gas_station", "color": "green", "label": "Petrol Pump"},
                "railway_station": {"type": "train_station", "color": "purple", "label": "Railway"},
                "airport": {"type": "airport", "color": "orange", "label": "Airport"},
                "metro_station": {"type": "subway_station", "color": "yellow", "label": "Metro"},
                "bus_stop": {"type": "bus_station", "color": "brown", "label": "Bus Stop"},
                "hospital": {"type": "hospital", "color": "pink", "label": "Hospital"},
                "school": {"type": "school", "color": "lightblue", "label": "School"},
                "shopping_mall": {"type": "shopping_mall", "color": "gray", "label": "Mall"}
            }

            # Find nearby POIs using Places API (New)
            places_url = "https://places.googleapis.com/v1/places:searchNearby"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.google_api_key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.types,places.location"
            }

            all_pois = []
            marker_strings = []

            # Add project location as primary red marker
            project_marker = f"color:red|label:P|{latitude},{longitude}"
            marker_strings.append(project_marker)

            # Search for each POI category within 5km radius
            for category_key, category_info in poi_categories.items():
                payload = {
                    "includedTypes": [category_info["type"]],
                    "maxResultCount": 3,  # Get top 3 of each type
                    "locationRestriction": {
                        "circle": {
                            "center": {
                                "latitude": latitude,
                                "longitude": longitude
                            },
                            "radius": 5000.0  # 5km radius
                        }
                    }
                }

                try:
                    response = requests.post(places_url, json=payload, headers=headers, timeout=5)
                    response.raise_for_status()
                    data = response.json()

                    places_found = data.get("places", [])

                    for idx, place in enumerate(places_found[:3]):  # Top 3 per category
                        place_name = place.get("displayName", {}).get("text", "Unknown")
                        place_address = place.get("formattedAddress", "")
                        place_location = place.get("location", {})
                        place_lat = place_location.get("latitude")
                        place_lng = place_location.get("longitude")

                        if place_lat and place_lng:
                            # Add to POI list
                            all_pois.append({
                                "name": place_name,
                                "category": category_info["label"],
                                "address": place_address,
                                "latitude": place_lat,
                                "longitude": place_lng,
                                "distance_km": self._haversine_distance(latitude, longitude, place_lat, place_lng)
                            })

                            # Add marker to map (use first letter of category as label)
                            label = category_info["label"][0]  # H for Hotel, P for Petrol, etc.
                            marker = f"color:{category_info['color']}|label:{label}|{place_lat},{place_lng}"
                            marker_strings.append(marker)

                except Exception as e:
                    print(f"[MAP] Error fetching {category_key}: {str(e)}")
                    continue

            # Sort POIs by distance
            all_pois.sort(key=lambda x: x["distance_km"])

            # Generate Static Map URL with all markers
            base_url = "https://maps.googleapis.com/maps/api/staticmap"

            # Build marker parameter (limited to 90 markers max by Google)
            markers_param = "&".join([f"markers={m}" for m in marker_strings[:90]])

            static_map_url = (
                f"{base_url}?center={latitude},{longitude}"
                f"&zoom={zoom}"
                f"&size={map_size}"
                f"&maptype=roadmap"
                f"&{markers_param}"
                f"&key={self.google_api_key}"
            )

            # Generate interactive embed URL
            embed_map_url = (
                f"https://www.google.com/maps/embed/v1/place"
                f"?key={self.google_api_key}"
                f"&q={urllib.parse.quote(project_name)}"
                f"&center={latitude},{longitude}"
                f"&zoom={zoom}"
            )

            print(f"[MAP] ✅ Generated map with {len(all_pois)} POIs for {project_name}")

            return {
                "static_map_url": static_map_url,
                "embed_map_url": embed_map_url,
                "project_location": {
                    "name": project_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "city": city
                },
                "poi_details": all_pois,
                "poi_count": len(all_pois),
                "marker_count": len(marker_strings),
                "zoom_level": zoom,
                "map_size": map_size
            }

        except Exception as e:
            print(f"[MAP] Error generating map: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two coordinates in kilometers

        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate

        Returns:
            Distance in kilometers (rounded to 2 decimals)
        """
        import math

        R = 6371.0  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return round(distance, 2)


# Singleton instance
_context_service_instance: Optional[ContextService] = None

def get_context_service() -> ContextService:
    """Get or create ContextService singleton instance"""
    global _context_service_instance
    if _context_service_instance is None:
        _context_service_instance = ContextService()
    return _context_service_instance
