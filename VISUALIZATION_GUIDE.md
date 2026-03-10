# Chat Visualization Guide

## Overview

The system automatically displays interactive charts in the chat when you ask comparison or ranking questions. No special commands needed - just ask naturally!

## Supported Visualizations

### 1. Heat-Maps (Spatial Comparison)

**When to use:** Compare projects across locations with geographic context

**Trigger keywords:**
- compare, comparison, across, all projects
- heat, map, location, geography, spatial
- show me, visualize, display

**Supported metrics:**
- `price` / `psf` → Current Price PSF (INR/sqft)
- `supply` / `units` → Total Supply Units
- `sold` → Sold Units
- `unsold` → Unsold Units
- `revenue` → Total Revenue
- `absorption` → Absorption Rate
- `velocity` → Sales Velocity

**Example questions:**
```
✅ "Compare prices across all projects in Chakan"
   → Heat-map with 9 projects in Chakan, color-coded by PSF

✅ "Show me supply across all locations"
   → Heat-map with all 10 projects, color-coded by total units

✅ "Heat map of unsold units"
   → Heat-map showing inventory distribution

✅ "Which projects have the highest prices?"
   → Heat-map with PSF visualization

❌ "What is the PSF of Sara City?"
   → No heat-map (single project, not a comparison)
```

**Output format:**
- Interactive Plotly scatter_mapbox
- Color gradient: Red (low) → Yellow → Green (high)
- Hover shows: Project name, location, metric value, coordinates
- Auto-centered and zoomed to fit all projects

---

### 2. Bar Charts (Rankings)

**When to use:** Rank or compare projects by a metric

**Trigger keywords:**
- top, bottom, highest, lowest
- best, worst, rank, ranking

**Example questions:**
```
✅ "Top 3 projects by project size"
   → Vertical bar chart with 3 projects

✅ "Rank all projects by revenue"
   → Bar chart sorted by revenue

✅ "Bottom 5 by absorption rate"
   → Bar chart with lowest 5 projects

✅ "Which projects have the highest supply?"
   → Bar chart sorted descending
```

**Output format:**
- Vertical bar chart with color gradient
- Bars sorted by value (descending for "top", ascending for "bottom")
- Values displayed on top of each bar
- Auto-limited if number specified in question (e.g., "top 3")

---

### 3. Line Charts (Trends) - *Coming Soon*

**When to use:** Show trends over time

**Trigger keywords:**
- trend, over time, timeline, growth, change
- history, progression

**Example questions (future):**
```
⏳ "Show me sales velocity trend for Sara City"
⏳ "Price growth over last 4 quarters"
⏳ "Absorption rate timeline"
```

---

### 4. Pie Charts (Distribution) - *Coming Soon*

**When to use:** Show breakdown or composition

**Trigger keywords:**
- breakdown, distribution, composition
- percentage, share, mix

**Example questions (future):**
```
⏳ "Unit type breakdown for Sara City"
⏳ "Project distribution by location"
⏳ "Sold vs unsold percentage"
```

---

## Technical Details

### Backend API

**Endpoint:** `GET /api/maps/heat-map`

**Parameters:**
- `metric` (required): Attribute name (e.g., `currentPricePSF`, `totalSupplyUnits`)
- `region` (optional): Location filter (e.g., `Chakan`, `Talegaon`)

**Response:**
```json
{
  "status": "success",
  "count": 9,
  "metric": "currentPricePSF",
  "region": "Chakan",
  "projects": [
    {
      "projectId": 3306,
      "projectName": "Sara City",
      "latitude": 18.7556934,
      "longitude": 73.8367202,
      "metric_value": 3996,
      "metric_name": "currentPricePSF",
      "metric_unit": "INR/sqft",
      "location": "Chakan",
      "microMarket": null
    },
    ...
  ]
}
```

### Data Source

- **Coordinates:** Google Maps Geocoding API (stored as L0 attributes)
- **Metrics:** Liases Foras knowledge graph (v4_clean_nested_structure.json)
- **Enrichment:** Automatic at data load time (10 projects geocoded, 100% success rate)

### Rendering Architecture

1. **Chart Detection** (`frontend/components/map_renderer.py:detect_chart_type()`)
   - Keyword-based pattern matching
   - Extracts metric, region, chart type from natural language

2. **Data Fetching** (if heat-map)
   - Calls `/api/maps/heat-map` with detected parameters
   - Returns geocoded projects with metric values

3. **Chart Rendering** (`frontend/components/map_renderer.py:render_heat_map()`)
   - Plotly scatter_mapbox for interactive heat-maps
   - Plotly Bar/Line/Pie for other chart types

4. **Chat Integration** (`frontend/streamlit_app.py:871-890`)
   - Automatically detects chart-worthy questions
   - Renders chart below text answer
   - Visual separator (horizontal rule) before chart

---

## Performance

- **API Response:** <50ms (coordinates pre-geocoded)
- **Chart Rendering:** <200ms (Plotly client-side)
- **Total Overhead:** <300ms added to query response time

---

## Customization

### Adding New Metrics

Edit `frontend/components/map_renderer.py:625-636`:

```python
metric_mapping = {
    "price": "currentPricePSF",
    "psf": "currentPricePSF",
    # Add your metric:
    "irr": "internalRateOfReturn",
    "npv": "netPresentValue",
}
```

### Adding New Trigger Keywords

Edit `frontend/components/map_renderer.py:599-613`:

```python
ranking_keywords = ["top", "bottom", "best", "worst", "rank", "ranking", "highest", "lowest"]
spatial_keywords = ["map", "heat", "location", "geography", "spatial", "across", "compare all"]
# Add your keywords
```

---

## Troubleshooting

**Issue:** Heat-map not displaying

**Causes:**
1. No comparison keywords in question → Add "compare", "across", or "all projects"
2. Projects missing coordinates → Check geocoding status in backend logs
3. Metric not recognized → Check `metric_mapping` in `map_renderer.py`

**Issue:** Wrong metric displayed

**Solution:** Be explicit in question:
- ❌ "Compare all projects" (defaults to PSF)
- ✅ "Compare supply across all projects" (uses totalSupplyUnits)

**Issue:** Region filter not working

**Solution:** Use exact region name from data:
- ✅ "Chakan" (works)
- ❌ "Chakan Area" (won't match)

---

## Future Enhancements

1. **Catchment Area Maps** - Draw radius around a point, list projects within
2. **Multi-Metric Charts** - Compare multiple metrics side-by-side
3. **Time Series** - Quarterly trends on line charts
4. **Custom Filters** - "Show projects above 4000 PSF"
5. **Export** - Download chart as PNG/SVG

---

## Examples Gallery

### Example 1: Price Comparison
**Question:** "Compare prices across all projects in Chakan"
**Output:**
- Text answer with statistics
- Heat-map showing 9 projects in Chakan
- Color scale: Red (₹3,189/sqft) to Green (₹4,330/sqft)

### Example 2: Supply Analysis
**Question:** "Show me total supply across all locations"
**Output:**
- Text answer listing projects
- Heat-map with all 10 projects
- Color scale based on unit count

### Example 3: Rankings (when bar charts active)
**Question:** "Top 3 projects by project size"
**Output:**
- Text answer with top 3 names
- Bar chart showing sizes
- Color gradient: darker = larger

---

**Need help?** Ask questions with keywords like "compare", "top", "map", "across" to trigger visualizations!
