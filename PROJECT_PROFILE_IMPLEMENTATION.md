# Project Profile Feature - Implementation Guide

## ✅ What's Been Created

### 1. New Component File
**File:** `frontend/components/project_profile.py`

**Functions:**
- `render_google_map(lat, lon, name, zoom)` - Embeds Google Map
- `render_photo_carousel(photos, name)` - Shows project photos
- `render_metadata_card(project_data)` - Beautiful header card with metadata
- `render_key_stats(project_data)` - 6-stat grid display
- `render_suggested_questions(name, location)` - Follow-up question suggestions
- `detect_location_query(question)` - Detects "where is" queries
- `detect_project_overview_query(question)` - Detects "tell me about" queries

---

## 🎯 Features to Implement

### Feature 1: Location Query → Google Maps Embed
**Trigger Questions:**
- "Where is Sara City?"
- "Location of Gulmohar City"
- "Show me The Urbana on map"

**Behavior:**
1. Detect location query using `detect_location_query()`
2. Extract project name
3. Fetch coordinates from KG
4. Call `render_google_map(latitude, longitude, project_name)`

**Integration Point:** `frontend/streamlit_app.py` (after text answer display)

```python
from components.project_profile import detect_location_query, render_google_map

# After displaying text answer
if idx > 0 and message["role"] == "assistant":
    user_message = st.session_state.messages[idx - 1]
    if user_message["role"] == "user":
        user_question = user_message["content"]

        # Check if location query
        if detect_location_query(user_question):
            # Extract project data from KG (pseudo-code)
            project_data = get_project_data(extract_project_name(user_question))
            lat = project_data.get('latitude', {}).get('value')
            lon = project_data.get('longitude', {}).get('value')
            name = project_data.get('projectName', {}).get('value')

            if lat and lon:
                render_google_map(lat, lon, name)
```

---

### Feature 2: Project Overview → Comprehensive Profile
**Trigger Questions:**
- "Tell me about Sara City"
- "What is Gulmohar City?"
- "Sara City details"

**Behavior:**
1. Detect overview query using `detect_project_overview_query()`
2. Extract project name
3. Fetch full project data from KG
4. Fetch photos using Google Custom Search API
5. Calculate performance metrics
6. Compare with area projects
7. Render components in order:
   - Metadata card (`render_metadata_card()`)
   - Google Maps embed (`render_google_map()`)
   - Photo carousel (`render_photo_carousel()`)
   - Key stats grid (`render_key_stats()`)
   - Performance analysis (text from LLM)
   - Area comparison (text from LLM)
   - Suggested questions (`render_suggested_questions()`)

**Integration Point:** Similar to Feature 1, but more comprehensive

---

## 📸 Photo Carousel Implementation

### Backend Endpoint Needed
**File:** `app/main.py`

```python
@app.get("/api/project/photos/{project_id}")
def get_project_photos(project_id: int):
    """
    Fetch project photos using Google Custom Search API

    Returns:
        List of image URLs
    """
    # Use GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX from env
    # Query: "[project_name] [developer_name] [location] residential project"
    # Filter: imageType=photo
    # Return: List of image URLs
    pass
```

**Google Custom Search API Call:**
```python
import requests

def fetch_project_photos(project_name: str, developer_name: str, location: str) -> List[str]:
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")

    query = f"{project_name} {developer_name} {location} residential project"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "searchType": "image",
        "num": 6,  # Get 6 photos
        "imgSize": "large",
        "safe": "active"
    }

    response = requests.get(url, params=params)
    data = response.json()

    photos = []
    if "items" in data:
        for item in data["items"]:
            photos.append(item["link"])

    return photos
```

---

## 📊 Performance Analysis & Area Comparison

### Add to LLM Prompt Template
**File:** `app/adapters/atlas_performance_adapter.py`

Add new query pattern:

```
• "Tell me about [Project]" / "What is [Project]" / "[Project] details" → COMPREHENSIVE PROJECT OVERVIEW

  MANDATORY RESPONSE FORMAT (7 SECTIONS):

  Section 1: TEXT SUMMARY (from LLM)
  Brief description of the project (2-3 sentences)

  [Then visual components are rendered by Streamlit - metadata card, map, photos, stats]

  Section 2: PERFORMANCE ANALYSIS
  "**Performance Analysis:**

  [Project Name] has achieved [X]% sales over [Y] years since launch. Key highlights:
  - **Absorption Rate:** [value]% annually ([interpretation: strong/moderate/weak])
  - **Sales Velocity:** [value] units/month ([interpretation])
  - **Price Growth:** [launch PSF] → [current PSF] ([%]% increase over [years] years)

  **Assessment:** [Overall performance rating: Excellent/Good/Average/Below Average]
  **Reason:** [Data-driven explanation using absorption, velocity, price trends]"

  Section 3: AREA COMPARISON
  "**Comparison with [Location] Market:**

  [Project Name] ranks [position] out of [total] projects in [Location] for:
  - **PSF:** [current PSF] vs Market Avg [avg PSF] ([above/below] by [%]%)
  - **Absorption:** [absorption]% vs Market Avg [avg]% ([above/below] by [%]%)
  - **Supply:** [units] units ([X]% of total [Location] supply)

  **Top Projects in Area:**
  1. [Project 1] - PSF: [value], Absorption: [value]%
  2. [Project 2] - PSF: [value], Absorption: [value]%
  3. [Project 3] - PSF: [value], Absorption: [value]%

  **Market Position:** [Above Average/Average/Below Average] - [Explanation]"

  Section 4: REASONS FOR PERFORMANCE
  "**Why is [Project] performing [well/poorly]?**

  Based on data analysis:
  1. [Factor 1 with data support]
  2. [Factor 2 with data support]
  3. [Factor 3 with data support]"

  [Then Streamlit renders Suggested Questions component]
```

---

## 🚀 Implementation Steps

### Step 1: Add Google Maps Embed (Quick Win)
1. Import `render_google_map` in `streamlit_app.py`
2. Add detection logic after text answer
3. Fetch coordinates from KG
4. Call `render_google_map()`

**Estimated Time:** 15 minutes

### Step 2: Add Photo Carousel
1. Create `/api/project/photos/{project_id}` endpoint
2. Implement Google Custom Search API call
3. Import `render_photo_carousel` in Streamlit
4. Call after map embed

**Estimated Time:** 30 minutes

### Step 3: Add Metadata Card & Stats
1. Import components in Streamlit
2. Fetch full project data from KG
3. Call `render_metadata_card()` and `render_key_stats()`

**Estimated Time:** 10 minutes

### Step 4: Enhance LLM Prompt
1. Add comprehensive overview template to `atlas_performance_adapter.py`
2. Include performance analysis section
3. Include area comparison section
4. Include reasons for performance

**Estimated Time:** 20 minutes

### Step 5: Add Suggested Questions
1. Import `render_suggested_questions` in Streamlit
2. Call at end of profile display

**Estimated Time:** 5 minutes

---

##Human: continue