# API Keys Setup Guide

This guide explains how to set up API keys for the Context Panel features (Maps, Images, Weather, News).

## Overview

The system works with **graceful fallbacks** - even without API keys, you'll get:
- Google Maps search links (instead of embedded maps)
- Placeholders for images
- "Unknown" weather status
- Google News search links

For full functionality, you'll need API keys for:
1. Google Maps (location visualization)
2. Google Custom Search (image collage)
3. OpenWeather (weather data)
4. NewsAPI (latest news)

---

## 1. Google Maps API

**Purpose**: Display interactive maps and static map images for locations/projects

**Setup Steps**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable these APIs:
   - **Maps Static API** (for static images)
   - **Maps Embed API** (for interactive embeds)
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → API Key**
6. Copy the API key
7. (Optional but recommended) Restrict the key:
   - Click on the key name
   - Under "API restrictions", select "Restrict key"
   - Choose "Maps Static API" and "Maps Embed API"
   - Under "Application restrictions", add your domain

**Add to `.env`**:
```bash
GOOGLE_MAPS_API_KEY=AIzaSy...your_key_here
```

**Free Tier**: $200/month credit (≈28,000 static map loads)

---

## 2. Google Custom Search API

**Purpose**: Fetch location/project images for visual context

**Setup Steps**:

### Part A: Create Custom Search Engine
1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **Add** to create new search engine
3. Configuration:
   - **Sites to search**: Leave empty or use "*" for entire web
   - **Name**: "Liases Foras Image Search"
   - **Image search**: Turn ON
   - **SafeSearch**: ON (recommended)
4. Click **Create**
5. Copy the **Search engine ID** (looks like: `017576662512468239146:omuauf_lfve`)

### Part B: Enable API & Get API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Custom Search API**
3. Go to **APIs & Services → Credentials**
4. Use existing API key or create new one
5. (Optional) Restrict to "Custom Search API" only

**Add to `.env`**:
```bash
GOOGLE_SEARCH_API_KEY=AIzaSy...your_key_here
GOOGLE_SEARCH_CX=017576662512468239146:omuauf_lfve
```

**Free Tier**: 100 search queries/day (Paid: $5 per 1000 queries after that)

---

## 3. OpenWeather API

**Purpose**: Display current weather for locations

**Setup Steps**:
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Navigate to **API keys** section
4. Copy the default API key (or create new one)
5. Wait ~10 minutes for key activation

**Add to `.env`**:
```bash
OPENWEATHER_API_KEY=a1b2c3d4e5...your_key_here
```

**Free Tier**: 1,000 API calls/day, 60 calls/minute

---

## 4. NewsAPI

**Purpose**: Fetch latest news about regions and projects

**Setup Steps**:
1. Go to [NewsAPI.org](https://newsapi.org/)
2. Click **Get API Key**
3. Sign up (free tier available)
4. Copy your API key from dashboard

**Add to `.env`**:
```bash
NEWS_API_KEY=a1b2c3d4e5...your_key_here
```

**Free Tier**:
- 100 requests/day
- Developer tier (free)
- Delays of up to 15 minutes for news

**Alternatives** (if you need more):
- Google News API (paid, but more quota)
- Build custom web scraper for Google News RSS

---

## Setup Instructions

### 1. Create `.env` file
```bash
cd /Users/tusharsikand/Documents/Projects/liases-foras
cp .env.example .env
```

### 2. Edit `.env` and add your API keys
```bash
# Open in your favorite editor
nano .env
# or
code .env
```

### 3. Add all keys
```bash
# Google APIs
GOOGLE_MAPS_API_KEY=AIzaSy...
GOOGLE_SEARCH_API_KEY=AIzaSy...
GOOGLE_SEARCH_CX=01757666...

# Weather
OPENWEATHER_API_KEY=a1b2c3d4...

# News
NEWS_API_KEY=a1b2c3d4...
```

### 4. Restart servers
```bash
# Kill existing servers
lsof -ti:8000 | xargs kill -9
lsof -ti:8501 | xargs kill -9

# Restart
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
python3 -m streamlit run frontend/streamlit_app.py --server.port 8501 --server.headless true &
```

---

## Cost Estimation

For typical usage (100 users/day, 10 queries each):

| Service | Free Tier | Typical Usage | Estimated Cost |
|---------|-----------|---------------|----------------|
| Google Maps | $200/month | ~1000 map loads/day | **$0** (within free tier) |
| Google Custom Search | 100/day free | ~500 images/day | **~$10/month** |
| OpenWeather | 1000/day free | ~500 calls/day | **$0** (within free tier) |
| NewsAPI | 100/day free | ~300 calls/day | **$0** (free tier) or $449/month (pro) |

**Total**: ~$10/month (or $459/month with NewsAPI Pro)

---

## Testing API Keys

After setup, test each service:

```python
# Test in Python
import os
from dotenv import load_dotenv
from app.services.context_service import get_context_service

load_dotenv()

# Test context service
context_service = get_context_service()
result = context_service.get_location_context("Chakan, Pune", location_type="region", city="Pune")

# Check results
print(f"Map URL: {result['map'].get('static_url') or 'Not available'}")
print(f"Images: {len(result['images'])} found")
print(f"Weather: {result['weather'].get('temperature')}°C" if result['weather'].get('temperature') else "Weather: Not available")
print(f"News: {len(result['news'])} articles")
```

---

## Troubleshooting

### Google Maps not showing
- Check API key is correct
- Verify "Maps Static API" and "Maps Embed API" are enabled
- Check API key restrictions aren't blocking requests
- Wait 5-10 minutes after creating key

### Images not loading
- Verify both `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_CX` are set
- Check Custom Search Engine has "Image search" enabled
- Ensure API key has "Custom Search API" enabled
- Check you haven't exceeded 100 queries/day

### Weather showing "Unknown"
- Verify `OPENWEATHER_API_KEY` is set
- Wait 10+ minutes after creating API key
- Check location name is valid (try "Mumbai" or "Pune")
- Verify you haven't exceeded rate limits

### News not loading
- Verify `NEWS_API_KEY` is set
- Check you haven't exceeded 100 requests/day
- For production, consider upgrading to paid plan
- Alternative: Use Google News RSS (no API key needed, but less features)

---

## Production Recommendations

1. **Use environment variables** (not hardcoded keys)
2. **Enable API key restrictions** (domain, IP, API limits)
3. **Monitor usage** via Google Cloud Console
4. **Set up billing alerts** (Google Cloud → Billing → Budgets)
5. **Implement caching** to reduce API calls:
   - Cache maps for 24 hours
   - Cache images for 7 days
   - Cache weather for 30 minutes
   - Cache news for 1 hour
6. **Rate limiting** on your end to prevent abuse
7. **Fallback gracefully** when quotas exceeded

---

## Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use different keys for dev/prod**
   ```bash
   # .env.development
   GOOGLE_MAPS_API_KEY=dev_key_here

   # .env.production
   GOOGLE_MAPS_API_KEY=prod_key_here
   ```

3. **Rotate keys periodically** (every 90 days recommended)

4. **Monitor for unusual activity** in Google Cloud Console

5. **Restrict keys** to specific APIs and domains

---

## Support

For issues:
1. Check [Google Maps API docs](https://developers.google.com/maps/documentation)
2. Check [OpenWeather API docs](https://openweathermap.org/api)
3. Check [NewsAPI docs](https://newsapi.org/docs)
4. Open issue in project repository
