# Quick Test Guide - Interactive Visualizations

## 🎯 How to Test (30 seconds)

### 1. Open Streamlit Chat
```
http://localhost:8501
```

### 2. Ask Any of These Questions

#### Heat-Maps (Will Show Interactive Map) 🗺️

```
Compare prices across all projects in Chakan
```
**Expected:** Text answer + Interactive heat-map with 9 projects color-coded by PSF (₹2,808 - ₹4,330)

```
Show me supply across all locations
```
**Expected:** Text answer + Heat-map with all 10 projects color-coded by total units

```
Heat map of unsold units
```
**Expected:** Text answer + Heat-map showing inventory distribution

---

#### Bar Charts (Framework Ready, Data Aggregation Needed) 📊

```
Top 3 projects by project size
```
**Expected:** Detection works, but needs backend aggregation endpoint

---

#### No Chart (Text Only - By Design) 📝

```
What is the PSF of Sara City?
```
**Expected:** Text answer only (no chart - single project query)

```
How many units does Sara City have?
```
**Expected:** Text answer only (no chart - single project query)

---

## ✅ What to Verify

### For Heat-Maps

1. **Text Answer Appears First** - Should display textual statistics
2. **Visual Separator** - Horizontal line (---) before chart
3. **Chart Title** - "📊 Visualization" header
4. **Interactive Map** - OpenStreetMap base layer
5. **Colored Markers** - Projects color-coded (Red = low, Green = high)
6. **Hover Details** - Project name, location, PSF value, coordinates
7. **Color Legend** - Shows metric scale on right side
8. **Auto-Zoom** - Map automatically centers on all projects

### For Text-Only Responses

1. **No Chart Displayed** - Should not show visualization for single-project queries
2. **Clean Answer** - Just the text response, no extra UI elements

---

## 🧪 Backend API Direct Test

### Test Heat-Map Endpoint Directly

```bash
# All projects in Chakan with PSF values
curl "http://localhost:8000/api/maps/heat-map?metric=currentPricePSF&region=Chakan" | jq

# All projects (no region filter) with supply values
curl "http://localhost:8000/api/maps/heat-map?metric=totalSupplyUnits" | jq

# All projects with absorption rate
curl "http://localhost:8000/api/maps/heat-map?metric=absorptionRate" | jq
```

**Expected Response:**
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

---

## 🐛 Troubleshooting

### Issue: Heat-Map Not Displaying

**Possible Causes:**
1. Question doesn't contain trigger keywords ("compare", "across", "map", "heat")
2. Streamlit session state issue

**Fix:**
- Add explicit keywords: "Compare prices **across all projects**"
- Refresh Streamlit page (F5)

---

### Issue: Chart Shows But No Data

**Possible Causes:**
1. Backend API not running
2. No projects with coordinates

**Fix:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check heat-map endpoint
curl "http://localhost:8000/api/maps/heat-map?metric=currentPricePSF"
```

---

### Issue: Wrong Metric Displayed

**Cause:** Metric keyword not detected

**Fix:** Be explicit in question:
- ❌ "Compare all projects" (defaults to PSF)
- ✅ "Compare **supply** across all projects" (uses totalSupplyUnits)

---

## 📊 Supported Metrics

| Say This... | Gets This Metric | Unit |
|-------------|------------------|------|
| price, psf | currentPricePSF | INR/sqft |
| supply, units | totalSupplyUnits | Units |
| sold | soldUnits | Units |
| unsold | unsoldUnits | Units |
| revenue | totalRevenue | INR Cr |
| absorption | absorptionRate | %/year |
| velocity | salesVelocity | Units/month |

---

## 🚀 Quick Start (Copy-Paste)

### 1. Ensure Servers Running
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend
open http://localhost:8501
```

### 2. Test Question
```
Compare prices across all projects in Chakan
```

### 3. Expected Result
✅ Text answer with statistics
✅ Horizontal separator line
✅ "📊 Visualization" header
✅ Interactive heat-map with 9 projects
✅ Color scale: Red (₹2,808) → Green (₹4,330)
✅ Hover shows: Project name, PSF, coordinates

---

## ⏱️ Performance Expectations

| Operation | Expected Time |
|-----------|---------------|
| Chart detection | <1ms |
| API call | <50ms |
| Plotly rendering | <200ms |
| Total overhead | <300ms |
| **Complete response** | **~1-2 seconds** |

---

## 📁 Test Data Coverage

- **Total Projects:** 10
- **Geocoded:** 10 (100%)
- **Projects in Chakan:** 9
- **PSF Range (Chakan):** ₹2,808 - ₹4,330
- **Average PSF (Chakan):** ~₹3,600

---

**Ready to test!** 🎉

Open Streamlit → Ask: *"Compare prices across all projects in Chakan"* → See the magic! ✨
