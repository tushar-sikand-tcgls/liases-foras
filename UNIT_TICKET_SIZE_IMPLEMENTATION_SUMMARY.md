# Unit Ticket Size Analysis - Implementation Summary

**Date:** 2025-01-24
**Status:** ✅ Complete
**Layer:** Pillar 2 - Product Performance

## Overview

Successfully integrated **Unit Ticket Size Analysis** into the knowledge graph system with full Layer 0, Layer 1, and Layer 2 derivative calculations. This enables sophisticated querying of market performance segmented by price ranges (ticket sizes in INR Lakhs).

---

## 📊 Data Structure

### Source Data
- **File:** `data/extracted/unit_ticket_size_analysis.json`
- **Price Ranges:** 5 ranges from <10 Lacs to 40-50 Lacs
- **Location:** Chakan, Pune, Maharashtra
- **Analysis Type:** Price-based market segmentation

### Data Layers

#### **Layer 0: Raw Dimensions** (U, CF, %, T)
```json
{
  "annual_sales_units": 569,              // U (Units)
  "annual_sales_value_pct": 16.34,       // % (Value proportion)
  "sales_units": 97,                      // U (Current sales)
  "sales_value_pct": 2.34,               // % (Current value)
  "unsold_units": 1453,                   // U (Unsold inventory)
  "unsold_value_pct": 32.68,             // % (Unsold value)
  "total_supply_units": 4240,             // U (Total supply)
  "total_supply_value_pct": 32.60,       // % (Supply value)
  "wt_avg_saleable_area_price_psf": 2812, // CF/L² (Price per sqft)
  "product_efficiency_pct": 56,           // % (Efficiency)
  "annual_months_inventory": 13           // T (Time to sell)
}
```

#### **Layer 1: Derived Metrics** (Simple Ratios)
Calculated automatically by `UnitTicketSizeService._calculate_layer1()`:

| Metric | Formula | Dimension |
|--------|---------|-----------|
| **Value Absorption Rate** | `(Annual Sales Value % / Total Supply Value %) × 100` | `%/% × 100 → %` |
| **Unit Absorption Rate** | `(Annual Sales Units / Total Supply Units) × 100` | `U/U × 100 → %` |
| **Value to Unit Ratio** | `Annual Sales Value % / Annual Sales Units` | `%/U → ratio` |
| **Unsold Value Concentration** | `(Unsold Value % / Total Supply Value %) × 100` | `%/% × 100 → %` |
| **Marketability Index** | `(Annual Marketable Supply Units / Total Supply Units) × 100` | `U/U × 100 → %` |
| **Price Premium Index** | `Wt Avg Saleable PSF / Market Avg PSF` | `CF/CF → ratio` |
| **Inventory Efficiency** | `1 / Annual Months Inventory` | `1/T → ratio` |
| **Monthly Sales Velocity** | `Quarterly Marketable Supply Units / 3` | `U/T → units/month` |
| **Supply to Sales Ratio** | `Total Supply Units / Annual Sales Units` | `U/U → ratio` |
| **Market Share by Value** | `(Total Supply Value % / Total Market Supply Value %) × 100` | `%/% × 100 → %` |

#### **Layer 2: Financial Metrics** (Complex Aggregations)
Calculated automatically by `UnitTicketSizeService._calculate_layer2()`:

| Metric | Formula | Dependencies |
|--------|---------|--------------|
| **Estimated Avg Unit Size** | `(Ticket Midpoint × 100000) / PSF` | Layer 0 |
| **Estimated Annual Sales Value** | `Annual Sales Units × Ticket Midpoint` | Layer 0 |
| **Revenue Concentration** | `(Sales Value % / Total Market Sales Value %) × 100` | Layer 0 |
| **Unsold Inventory Value** | `Unsold Units × Ticket Midpoint` | Layer 0 |
| **Market Capitalization** | `Total Supply Units × Ticket Midpoint` | Layer 0 |
| **Affordability Score** | `(Ticket Midpoint / Market Avg Income) × 100` | Layer 0 |
| **Annual Months Inventory** | Directly from Layer 0 | Layer 0 |
| **Quarterly Months Inventory** | Directly from Layer 0 | Layer 0 |
| **Price Efficiency Score** | `Product Efficiency % × Price Premium Index` | Layer 0, Layer 1 |
| **Annual Marketable Supply Value** | `Annual Marketable Supply Units × Ticket Midpoint` | Layer 0 |
| **Quarterly Marketable Supply Value** | `Quarterly Marketable Supply Units × Ticket Midpoint` | Layer 0 |
| **Investment Concentration** | `(Market Cap / Total Market Cap) × 100` | Layer 2 |

---

## 🔧 Service API

### UnitTicketSizeService

Located at: `app/services/unit_ticket_size_service.py`

#### Key Methods

```python
from app.services.unit_ticket_size_service import get_unit_ticket_size_service

service = get_unit_ticket_size_service()

# 1. Get all ticket ranges with derivatives
all_ranges = service.get_all_ticket_ranges()

# 2. Get specific range by ID
range_data = service.get_ticket_range_by_id("ticket_10_20")

# 3. Find range by price point
my_range = service.get_ticket_range_by_price(15)  # Returns 10-20 Lac range

# 4. Get top performers
top_3 = service.get_top_performing_ranges(metric="value_absorption_rate_pct", top_n=3)

# 5. Compare multiple ranges
comparison = service.compare_ticket_ranges(["ticket_below_10", "ticket_10_20"])

# 6. Get market summary
summary = service.get_summary_statistics()
```

#### Response Format

```json
{
  "ticket_range_id": "ticket_10_20",
  "ticket_size_range": "10 Lac - 20 Lac",
  "ticket_min_lacs": 10,
  "ticket_max_lacs": 20,

  "annual_sales_units": 325,
  "annual_sales_value_pct": 20.40,
  "total_supply_units": 1356,
  "total_supply_value_pct": 84.02,
  "product_efficiency_pct": 73,

  "layer1_derivatives": {
    "value_absorption_rate_pct": 24.29,
    "unit_absorption_rate_pct": 23.97,
    "value_to_unit_ratio": 0.0628,
    "marketability_index_pct": 92.63,
    "price_premium_index": 1.25
  },

  "layer2_derivatives": {
    "estimated_avg_unit_size_sqft": 426.14,
    "estimated_annual_sales_value_lacs": 4875.0,
    "market_capitalization_lacs": 20340.0,
    "affordability_score": 100.0,
    "price_efficiency_score": 91.25,
    "investment_concentration_pct": 28.5
  }
}
```

---

## 🧠 LLM Function Calling

### Available Functions

#### 1. **unit_ticket_size_lookup**
The primary function exposed to LLM for querying ticket size (price range) data.

**Function Schema:**
```json
{
  "name": "unit_ticket_size_lookup",
  "description": "Query Unit Ticket Size Knowledge Graph for price-based performance analysis",
  "parameters": {
    "price_lacs": "number (find range containing this price)",
    "min_efficiency": 0-100,
    "min_sales": "integer",
    "max_affordability": "number (lower = more affordable)",
    "top_n": "integer",
    "metric": "value_absorption_rate_pct | unit_absorption_rate_pct | product_efficiency_pct | price_efficiency_score"
  }
}
```

**Example Queries:**

| User Query | LLM Function Call | Result |
|------------|-------------------|--------|
| "What's the best performing price range?" | `{"top_n": 1, "metric": "product_efficiency_pct"}` | Top range by efficiency |
| "Show me affordable housing" | `{"price_lacs": 8}` | <10 Lac range |
| "Which price ranges have good value absorption?" | `{"min_efficiency": 50}` | Ranges with efficiency ≥ 50% |
| "15 Lakh units performance" | `{"price_lacs": 15}` | 10-20 Lac range |
| "Top 3 by value absorption" | `{"top_n": 3, "metric": "value_absorption_rate_pct"}` | Top 3 by value sales |

### Integration with Gemini

The function is automatically registered in `FunctionRegistry` and available for Gemini function calling:

```python
# Already integrated - no additional setup needed!
# Gemini can call this function directly

# Example LLM conversation:
User: "What's the affordability situation for mid-range housing?"

Gemini (internal):
  function_call: unit_ticket_size_lookup
  arguments: {"price_lacs": 15}

System → Returns 10-20 Lac range with Layer 0, 1, 2 metrics

Gemini (response):
  "The 10-20 Lac price range has strong performance in Chakan, Pune.
   With 325 annual sales (23.97% unit absorption) and 73% product efficiency,
   this is the top-performing segment. The affordability score is 100.0,
   indicating it's well-aligned with local income levels (assuming 15 Lakh avg income).
   The marketability index is 92.63%, showing strong market acceptance..."
```

---

## 📈 Key Metrics Available

### Performance Metrics
- ✅ **Value Absorption Rate** - Sales efficiency by value
- ✅ **Unit Absorption Rate** - Sales efficiency by units
- ✅ **Product Efficiency** - Supply utilization
- ✅ **Marketability Index** - Market acceptance
- ✅ **Inventory Efficiency** - Stock rotation speed

### Price Analysis
- ✅ **Value to Unit Ratio** - Value per unit sold
- ✅ **Price Premium Index** - Pricing vs market average
- ✅ **Price Efficiency Score** - Combined efficiency × premium

### Financial Metrics
- ✅ **Estimated Annual Sales Value** - Total revenue projection
- ✅ **Revenue Concentration** - Share of market revenue
- ✅ **Market Capitalization** - Total market value
- ✅ **Unsold Inventory Value** - Capital locked in unsold units
- ✅ **Investment Concentration** - Market share by value

### Affordability & Market Position
- ✅ **Affordability Score** - Price vs average income
- ✅ **Market Share by Value** - Value-based market share
- ✅ **Supply to Sales Ratio** - Supply vs demand balance
- ✅ **Months of Inventory** - Time to sell current stock

---

## 🎯 Use Cases

### 1. Affordability Analysis
**Query:** "Which price ranges are most affordable?"
```python
top_affordable = service.get_all_ticket_ranges()
sorted_by_affordability = sorted(
    [service._enrich_with_derivatives(tr) for tr in top_affordable],
    key=lambda x: x["layer2_derivatives"]["affordability_score"]
)
```
**Result:** Identify price ranges best suited to local income levels

### 2. Value vs Volume Analysis
**Query:** "Which price range generates the most value vs most units?"
```python
# Most units
top_units = service.get_top_performing_ranges(metric="unit_absorption_rate_pct", top_n=1)

# Most value
top_value = service.get_top_performing_ranges(metric="value_absorption_rate_pct", top_n=1)
```
**Result:** Distinguish between volume play vs premium strategy

### 3. Price Segmentation Strategy
**Query:** "Compare <10 Lac vs 10-20 Lac performance"
```python
comparison = service.compare_ticket_ranges(["ticket_below_10", "ticket_10_20"])
```
**Result:** Side-by-side comparison for pricing strategy decisions

### 4. Investment Concentration
**Query:** "Where is the most capital locked?"
```python
top_investment = service.get_top_performing_ranges(
    metric="market_capitalization_lacs",
    top_n=3
)
```
**Result:** Identify price ranges with highest capital allocation

### 5. Market Entry Analysis
**Query:** "Which price range has the best efficiency-affordability balance?"
```python
all_ranges = [service._enrich_with_derivatives(tr) for tr in service.get_all_ticket_ranges()]
balanced = [
    r for r in all_ranges
    if r["product_efficiency_pct"] > 50 and
       r["layer2_derivatives"]["affordability_score"] < 120
]
```
**Result:** Find sweet spot for market entry

---

## 🔄 Data Flow

```
User Query
    ↓
Gemini LLM (function calling)
    ↓
FunctionRegistry.unit_ticket_size_lookup
    ↓
UnitTicketSizeService
    ↓
Load Layer 0 from JSON
    ↓
Calculate Layer 1 (derived metrics)
    ↓
Calculate Layer 2 (financial metrics)
    ↓
Return enriched data
    ↓
Gemini formats natural language response
    ↓
User receives answer
```

---

## 🧪 Testing

### Quick Test
```bash
# Test service loading
python3 -c "from app.services.unit_ticket_size_service import get_unit_ticket_size_service; \
service = get_unit_ticket_size_service(); \
print('✅ Loaded', len(service.get_all_ticket_ranges()), 'ticket size ranges')"

# Test derivative calculations
python3 -c "from app.services.unit_ticket_size_service import get_unit_ticket_size_service; \
service = get_unit_ticket_size_service(); \
range_data = service.get_ticket_range_by_id('ticket_10_20'); \
print('✅ Value Absorption Rate:', range_data['layer1_derivatives']['value_absorption_rate_pct'], '%'); \
print('✅ Affordability Score:', range_data['layer2_derivatives']['affordability_score'])"
```

### Sample Queries to Test
```
1. "What is the best performing price range in Chakan?"
2. "Show me affordable housing options (<10 Lacs)"
3. "Which price ranges have high value absorption?"
4. "Compare 10-20 Lac vs 20-30 Lac performance"
5. "What's the affordability score for 15 Lakh units?"
6. "Which price range has the fastest inventory turnover?"
```

---

## 📝 Data Lineage

**Layer 0 → Layer 1 → Layer 2**

Every metric traces back to Layer 0 dimensions:

```
Layer 0: annual_sales_value_pct = 20.40% (%)
         total_supply_value_pct = 84.02% (%)
         annual_sales_units = 325 (U)
         ticket_midpoint = 15 Lacs (CF)

Layer 1: value_absorption_rate = (20.40 / 84.02) × 100 = 24.29% (%/%)
         marketability_index = (1256 / 1356) × 100 = 92.63% (U/U)

Layer 2: market_capitalization = 1356 × 15 = 20,340 Lacs (U × CF)
         affordability_score = (15 / 15) × 100 = 100.0 (CF/CF)
```

All calculations maintain dimensional consistency per the physics-inspired model.

---

## ✅ Verification

- [x] Data file loaded successfully (5 ticket size ranges)
- [x] Layer 0 raw dimensions accessible
- [x] Layer 1 derivatives calculated correctly (10 metrics)
- [x] Layer 2 financial metrics computed (12 metrics)
- [x] Function registered in FunctionRegistry
- [x] LLM function calling schema defined
- [x] Service handles all query types
- [x] Comparison and top-N queries working
- [x] Market summary statistics available
- [x] All tests passing (31 functions in registry)

---

## 🚀 Next Steps

### Enhancements
1. **Time-Series Analysis**: Add quarterly/monthly trends for each ticket range
2. **Cross-Location Comparison**: Compare same price ranges across different cities
3. **Price Elasticity**: Analyze how demand changes with price variations
4. **Demographic Alignment**: Match ticket sizes with income distribution data
5. **Alert System**: Flag price ranges with declining performance

### Integration
1. **Visualization**: Create chart service for ticket size performance
2. **Dashboard**: Add ticket size panel to Streamlit UI
3. **Export**: Generate PDF reports for price range analysis
4. **API Endpoints**: Add REST API for external access
5. **Cross-Analysis**: Integrate with Unit Size Range for combined insights

### Advanced Analytics
1. **Price-Size Correlation**: Analyze relationship between unit size and ticket size
2. **Optimal Pricing**: Recommend price points based on size and efficiency
3. **Market Segmentation**: Cluster buyers by affordability and preference
4. **Competitive Analysis**: Compare pricing strategy against peer projects

---

## 📚 Related Documentation

- **CLAUDE.md**: Project overview and architecture
- **Function Registry**: `app/services/function_registry.py` (lines 1822-1999)
- **Service Implementation**: `app/services/unit_ticket_size_service.py`
- **Data Source**: `data/extracted/unit_ticket_size_analysis.json`
- **Related System**: `UNIT_SIZE_RANGE_IMPLEMENTATION_SUMMARY.md` (size-based analysis)

---

**Status**: ✅ **Production Ready**
**Integration**: ✅ **LLM Function Calling Active**
**Testing**: ✅ **Verified**

The Unit Ticket Size Analysis system is now fully operational and queryable via natural language through Gemini function calling.
