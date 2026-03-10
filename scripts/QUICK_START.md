# Quick Start - Comprehensive Kolkata Enrichment

## Overview
Integrates **ALL 57 Excel files** from Kolkata R&D into a comprehensive v4 knowledge graph.

## Quick Execution

### Option 1: Run the Python script directly
```bash
cd /Users/tusharsikand/Documents/Projects/liases-foras
python3 scripts/comprehensive_kolkata_enrichment.py
```

### Option 2: Use the convenience shell script
```bash
cd /Users/tusharsikand/Documents/Projects/liases-foras
./scripts/comprehensive_kolkata_enrichment.sh
```

## Input/Output

**Input Directory:**
```
/Users/tusharsikand/Downloads/Kolkata R&D/
```
Contains 57 Excel files across 9 categories.

**Output File:**
```
/Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata/kolkata_v4_comprehensive.json
```

## File Categories Integrated

| Category | Files | Status |
|----------|-------|--------|
| Base Data | 1 | ✅ |
| Price Trends | 28 | ✅ |
| Sales Data | 7 | ✅ |
| Inventory & Stock | 4 | ✅ |
| Analysis | 5 | ✅ |
| Performance Metrics | 4 | ✅ |
| Supply Data | 2 | ✅ |
| Project Details | 3 | ✅ |
| Market Summary | 2 | ✅ |
| **TOTAL** | **57+** | **✅** |

## V4 Dimensions

- **U** - Units (count)
- **L²** - Area (square feet)
- **C** - Currency (Rs Lacs)
- **C/L²** - Price per area (Rs/sqft)
- **T** - Time (dates/quarters/years)
- **I** - Information (text/categorical)
- **L** - Location (geographic)
- **U/T** - Velocity (units per time)

## What Gets Enriched

### Project-Level Data
Each project gets enriched with:
- Base attributes (location, developer, dates, supply, sales)
- Price trend time series (when Project ID matches)
- Annual/quarterly sales time series (when available)
- Construction stage breakdowns
- Inventory and velocity metrics
- Unit mix and distributions
- Performance rankings (if in top 10)
- Wing/flatwise details

### Market-Level Data
The market_analysis section includes:
- Possession-wise distribution (11 periods)
- Quarterly supply summary (45 quarters)
- Quarterly market summary (14 quarters)
- Yearly market summary (11 years)
- Flat type distribution (31 types)
- Top performers (4 metric categories)

## Viewing the Output

### View metadata
```bash
cat data/extracted/kolkata/kolkata_v4_comprehensive.json | jq '.metadata'
```

### View first project
```bash
cat data/extracted/kolkata/kolkata_v4_comprehensive.json | jq '.page_2_projects[0]'
```

### View market analysis
```bash
cat data/extracted/kolkata/kolkata_v4_comprehensive.json | jq '.market_analysis'
```

### Count enrichments
```bash
cat data/extracted/kolkata/kolkata_v4_comprehensive.json | jq '.enrichment_metadata'
```

## Performance

- **Processing Time:** ~60 seconds
- **Output Size:** ~153 KB
- **Projects:** 5 base projects
- **Files Loaded:** 59 (includes variants)

## Error Handling

The script is designed to:
- Continue on individual file errors
- Auto-detect header rows in Excel files
- Handle missing or malformed data gracefully
- Log all processing steps

Check the console output for any warnings about files that couldn't be loaded.

## Next Steps

After running the enrichment:

1. **Verify Output:** Check that the JSON file was created
2. **Review Logs:** Look for any warnings in the console output
3. **Inspect Data:** Use `jq` to explore the structure
4. **Load into KG:** Use the output in your knowledge graph system

## Documentation

For detailed documentation, see:
- **Full Documentation:** `COMPREHENSIVE_ENRICHMENT_README.md`
- **Script Location:** `comprehensive_kolkata_enrichment.py`

## Troubleshooting

**Problem:** Script not found
```bash
# Make sure you're in the right directory
pwd  # Should show: /Users/tusharsikand/Documents/Projects/liases-foras
```

**Problem:** Input files not found
```bash
# Verify the input directory exists
ls -la "/Users/tusharsikand/Downloads/Kolkata R&D" | wc -l
# Should show 57+ files
```

**Problem:** Permission denied on shell script
```bash
chmod +x scripts/comprehensive_kolkata_enrichment.sh
```

## Support

Created: February 25, 2026
Version: 1.0
