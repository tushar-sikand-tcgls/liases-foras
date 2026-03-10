# Comprehensive Query Test Examples

## Overview

This document contains example queries across all supported query types: Simple L0 attributes, Calculated metrics, Math operations, SQL-like operations, Stats operations, Composite metrics, and Conversational queries.

## Test Categories

### 1. SIMPLE L0 ATTRIBUTES (Direct Extraction)

These queries fetch raw data directly from the knowledge graph without calculations.

```
✓ What is the Project Size of Sara City?
✓ What is the Total Supply for Gulmohar City?
✓ When was Sara City launched?
✓ What is the location of Shubhan Karoli?
✓ Is Gulmohar City RERA registered?
✓ What is the Launch Date for Sara City?
✓ What is the Developer Name for Gulmohar City?
✓ What is the Unit Saleable Size for Shubhan Karoli?
```

**Expected Output Format:**
- Bold answer with units
- Brief definition (if asked for calculated metric)
- Source attribution in italics

---

### 2. CALCULATED METRICS (L1 Derived - Single Project)

These queries calculate derived metrics for a specific project using formulas from Excel.

```
✓ What is the PSF Gap for Gulmohar City?
✓ What is MOI for Sara City?
✓ Calculate Months of Inventory for Shubhan Karoli
✓ What is the Price Growth percentage for Sara City?
✓ What is Effective Realised PSF for Shubhan Karoli?
✓ Calculate Unsold Units for Gulmohar City
✓ What is the Average Ticket Size for Sara City?
✓ What is Sold Units for Gulmohar City?
✓ Calculate Monthly Units Sold for Sara City
✓ What is the Annual Absorption Rate for Shubhan Karoli?
```

**Expected Output Format:**
- **Definition:** What the metric means
- **Formula:** The calculation formula
- **Calculation:** Step-by-step with input values
- **Result:** Bold answer with units
- **Insight:** Interpretation (if appropriate)
- **Source:** *Liases Foras* in italics

---

### 3. MATH OPERATIONS

#### Sum/Total
```
✓ What is the total supply across all projects?
✓ What is the sum of Annual Sales Units for all Chakan projects?
✓ Calculate total Project Size across all projects
✓ Sum of Sold Units across all projects
```

#### Average/Mean
```
✓ What is the average Launch Price PSF across all projects?
✓ What is the average Total Supply Units?
✓ Calculate average Current Price PSF for all projects
✓ What is the mean Unsold Percent across all projects?
```

#### Difference
```
✓ What is the difference between Sara City and Gulmohar City in Total Supply?
✓ Compare Annual Sales Units between Sara City and Gulmohar City
✓ PSF Gap difference between projects
```

#### Product/Division (Implicit)
```
✓ Calculate total saleable area across all projects  (Units × Size)
✓ What is total annual sales value?  (Units × PSF × Size)
```

---

### 4. SQL-LIKE OPERATIONS

#### Top-N Queries
```
✓ List top 3 projects by Launch Price PSF
✓ Show me the top 5 projects by Annual Sales Units
✓ Which project has the highest PSF Gap?
✓ Top 3 projects by Total Supply
✓ Which 3 projects have the lowest MOI?
✓ Top 5 projects by Sold Percent
```

#### Sorting/Ordering
```
✓ List all projects sorted by Current Price PSF descending
✓ Show projects ordered by Sold Percent
✓ Sort projects by Annual Sales Units (highest to lowest)
✓ Order projects by Unsold Percent ascending
```

#### Filters (Greater Than, Less Than)
```
✓ List all projects where Unsold Percent is greater than 10%
✓ Show projects with Annual Sales Units above 500
✓ Which projects have MOI less than 12 months?
✓ Find projects where Total Supply is greater than 700 units
✓ Show projects with Sold Percent below 30%
```

#### Range Filters (Between)
```
✓ Find projects where Sold Percent is between 30% and 50%
✓ Show projects with Total Supply between 500 and 1000 units
✓ List projects with Launch Price PSF between Rs 2000 and Rs 3000
✓ Which projects have Annual Sales Units between 400 and 600?
```

#### Combined Filters (AND/OR)
```
✓ Find projects with Unsold Percent < 20% AND Annual Sales > 400 units
✓ Show projects where MOI < 10 OR Annual Sales Units > 500
✓ Projects with high sales AND low inventory
```

---

### 5. STATS OPERATIONS (Aggregations)

#### Average/Mean
```
✓ What is the average Unsold Percent across all projects?
✓ Calculate mean Annual Sales Value for all projects
✓ Average MOI across all projects
✓ Mean Launch Price PSF
```

#### Median
```
✓ What is the median Total Supply Units?
✓ Find the median Launch Price PSF
✓ Calculate median Annual Sales Units
✓ Median Sold Percent across all projects
```

#### Min/Max
```
✓ Which project has the minimum Unsold Percent?
✓ What is the maximum Annual Sales Units?
✓ Find project with highest Current Price PSF
✓ Which project has the lowest MOI?
```

#### Count
```
✓ How many projects have Sold Percent above 50%?
✓ Count projects in Chakan location
✓ How many projects have negative PSF Gap?
✓ Count projects with MOI less than 10 months
```

---

### 6. COMPOSITE METRICS (Multi-step Calculations)

Queries that combine multiple L1 metrics or require multi-step reasoning.

```
✓ Show top 3 projects by PSF Gap and their MOI
✓ List projects with high absorption rate and low MOI
✓ Which projects have positive Price Growth and high Annual Sales?
✓ Compare Launch Price PSF to Current Price PSF for all projects
✓ Show projects where PSF Gap is negative (price dropped)
✓ Find projects with strong sales velocity but high unsold inventory
✓ Which projects have best price appreciation and low MOI?
```

**Complex Composite Examples:**
```
✓ Show projects where PSF Gap > 100 AND Sold Percent > 40%
✓ List projects with MOI < 15 months, PSF Gap > 0, and Annual Sales > 450 units
✓ Compare absorption rate vs inventory for all projects
```

---

### 7. CONVERSATIONAL QUERIES (Natural Language)

Natural, human-like queries that require understanding context and intent.

```
✓ Which project is selling the fastest?
✓ Show me projects that are doing well in sales
✓ Which projects might take longest to sell out?
✓ Are there any projects with pricing challenges?
✓ Which projects have the best absorption rates?
✓ Which project would you recommend for quick sellout?
✓ Are there any projects where prices have dropped?
✓ Show me projects with healthy inventory levels
✓ Which projects are overperforming in the market?
```

---

### 8. LOCATION-BASED QUERIES

Queries filtered by location/geography.

```
✓ List all projects in Chakan
✓ How many projects are in Pune?
✓ Compare all Chakan projects by Annual Sales Units
✓ Show average MOI for Chakan projects
✓ Which Chakan project has highest Sold Percent?
```

---

### 9. DEVELOPER-BASED QUERIES

Queries filtered by developer/builder.

```
✓ Which developer has the most projects?
✓ Show all projects by Creative Ventures
✓ Compare projects from different developers
✓ What is the average Sold Percent for Creative Ventures projects?
```

---

## Test Execution

### Quick Test (Manual - 5 minutes)

Test one query from each category:

1. **L0 Attribute:** "What is the Total Supply for Sara City?"
2. **Calculated Metric:** "What is the PSF Gap for Gulmohar City?"
3. **Math:** "What is the average Launch Price PSF across all projects?"
4. **SQL Top-N:** "List top 3 projects by Annual Sales Units"
5. **SQL Filter:** "Show projects where Unsold Percent > 10%"
6. **Stats:** "Which project has the maximum Annual Sales Units?"
7. **Composite:** "Show top 3 projects by PSF Gap and their MOI"
8. **Conversational:** "Which project is selling the fastest?"

### Automated Test (Python Script)

Run the comprehensive test suite:

```bash
python3 /tmp/test_comprehensive_queries.py
```

This will test:
- **60+ queries** across all categories
- **Rate-limited** to 2 seconds between queries
- **Detailed results** with timing and success rates

---

## Expected Output Examples

### Example 1: Simple L0 Attribute
**Q:** "What is the Total Supply for Sara City?"

**Expected:**
```
The Total Supply for Sara City is **770 units**.

*Source: Liases Foras*
```

---

### Example 2: Calculated Metric (PSF Gap)
**Q:** "What is the PSF Gap for Gulmohar City?"

**Expected:**
```
**Definition:**
PSF Gap represents the difference between the Launch Price PSF and Current Price PSF...

**Formula:**
PSF Gap = Launch Price PSF - Current Price PSF

**Calculation:**
• Launch Price PSF: **Rs.2,000/Sq.Ft.**
• Current Price PSF: **Rs.2,200/Sq.Ft.**
• PSF Gap = **Rs.2,000** - **Rs.2,200** = **-Rs.200/Sq.Ft.**

**Result:**
The PSF Gap for Gulmohar City is **-Rs.200/Sq.Ft.**

**Insight:**
Negative PSF Gap indicates price appreciation...

*Source: Liases Foras - Pricing Analytics Database*
```

---

### Example 3: SQL Top-N
**Q:** "List top 3 projects by Launch Price PSF"

**Expected:**
```
Here are the top 3 projects by Launch Price PSF:

1. **Shubhan Karoli** - Rs.2,500/Sq.Ft.
2. **Gulmohar City** - Rs.2,000/Sq.Ft.
3. **Sara City** - Rs.1,800/Sq.Ft.

*Source: Liases Foras*
```

---

### Example 4: Composite Metric
**Q:** "Show top 3 projects by PSF Gap and their MOI"

**Expected:**
```
Here are the top 3 projects by PSF Gap along with their Months of Inventory:

1. **Project X**
   - PSF Gap: **Rs.500/Sq.Ft.**
   - MOI: **8.2 months**

2. **Project Y**
   - PSF Gap: **Rs.350/Sq.Ft.**
   - MOI: **12.5 months**

3. **Project Z**
   - PSF Gap: **Rs.200/Sq.Ft.**
   - MOI: **6.8 months**

*Source: Liases Foras - Pricing Analytics & Sales Performance Database*
```

---

## Success Criteria

### For Each Query Type:

✅ **Response Time:** < 3 seconds
✅ **Format:** Matches expected structure (Definition, Formula, Calculation, Result, Insight, Source)
✅ **Accuracy:** Values match manual calculations
✅ **Source:** Always includes "*Source: Liases Foras*" in italics
✅ **Conversational:** Natural tone with insights (not just dry numbers)

### For Calculated Metrics:

✅ **Formula shown:** For compound metrics
✅ **Definition included:** Brief explanation of what's being calculated
✅ **Step-by-step calculation:** Input values → derivation → result
✅ **Units:** Always include proper units (Rs, units, %, months, etc.)

---

## Test Script Usage

### Run Quick Test (Subset)
```bash
python3 /tmp/test_comprehensive_queries.py
```

### Run Full Test Suite (All Queries - ~30 minutes)
Edit the script and uncomment:
```python
# Change from quick_test_queries to test_queries
results = run_all_tests()
```

### Test Single Query
```bash
curl -X POST http://localhost:8000/api/atlas/hybrid/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the PSF Gap for Gulmohar City?"}'
```

---

## Categories Summary

| Category | Query Count | Example |
|----------|-------------|---------|
| L0 Attributes | 8 | "What is Total Supply for Sara City?" |
| Calculated Metrics | 10 | "What is PSF Gap for Gulmohar City?" |
| Math Operations | 12 | "Average Launch Price PSF across all projects" |
| SQL-like (Top-N) | 6 | "Top 3 projects by Annual Sales Units" |
| SQL-like (Filters) | 10 | "Projects where Unsold Percent > 10%" |
| Stats Operations | 12 | "Median Total Supply Units" |
| Composite Metrics | 7 | "Top 3 by PSF Gap with their MOI" |
| Conversational | 9 | "Which project is selling the fastest?" |
| Location-based | 5 | "All projects in Chakan" |
| Developer-based | 4 | "Projects by Creative Ventures" |

**Total:** 83 example queries

---

*Use this as a reference for testing the system's capabilities across all query types.*
