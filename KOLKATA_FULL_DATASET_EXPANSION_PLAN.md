# Kolkata Full Dataset Expansion Plan

**Date:** 2025-12-29
**Request:** Load all Kolkata projects (not just 5) with complete L0/L1/L2 attribute schema
**Status:** 🔄 IN PROGRESS

---

## 📊 **Current State**

### **Existing Data:**
- **Projects Loaded**: 5 projects only
  1. Siddha Galaxia
  2. Merlin Verve
  3. PS Panache
  4. Srijan Eternis
  5. Ambuja Utalika

- **Metadata Claims**: 880 total projects exist (from `kolkata_projects.json` metadata)
- **Source Files**:
  - `/change-request/kolkata/Kolkata_R&D_Combined_Final.pdf` (59 pages)
  - `/change-request/managed-rag/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx` (attribute schema)

### **Current Attribute Coverage:**
The existing 5 projects have **partial** L0/L1 attributes. The Excel schema defines **36 total attributes** that should be present.

---

## 📋 **Complete Attribute Schema (from Excel)**

### **L0 Attributes (24 attributes - Raw Dimensions)**

| # | Attribute | Unit | Dimension | Description |
|---|-----------|------|-----------|-------------|
| 1 | Project Id | ID | - | Unique identifier for database tracking |
| 2 | Project Name | Text | - | Official marketing name |
| 3 | Developer Name | Text | - | Legal entity/organization |
| 4 | Location | Text | - | Geographic location (micromarket, city, state) |
| 5 | Launch Date | Month | T | Official opening date for bookings |
| 6 | Possession Date | Month | T | Expected handover date per RERA |
| 7 | Project Size | Units | U | Total units planned across all phases |
| 8 | Total Supply | Units | U | Saleable units launched and available |
| 9 | Sold (%) | % | - | Percentage of supply sold to date |
| 10 | Unsold (%) | % | - | Percentage of supply remaining unsold |
| 11 | Unit Saleable Size | Sq.ft. | L² | Average saleable area per unit |
| 12 | Monthly Sales Velocity | %/month | T⁻¹ | Average units sold per month |
| 13 | RERA Registered | Y/N | - | RERA registration status |
| 14 | Unsold Units | Units | U | Absolute unsold inventory |
| 15 | Sold Units | Units | U | Absolute units sold to date |
| 16 | Months of Inventory | Months | T | Time to clear unsold inventory at current rate |
| 17 | Price Growth (%) | % | - | Price appreciation from launch to current |
| 18 | Unsold Inventory Value | Rs Cr | C | Total value of unsold units |
| 19 | Annual Absorption Rate | % | - | % of unsold inventory absorbed annually |
| 20 | Future Sellout Time | Years | T | Time to 100% sellout at current rate |
| 21 | Annual Clearance Rate | % | - | % of unsold inventory cleared annually |
| 22 | Sellout Time | Years | T | Estimated time to achieve 100% sellout |
| 23 | Sellout Efficiency | % | - | Efficiency of converting inventory to sales |
| 24 | Price-to-Size Ratio | Rate | - | Current PSF / Unit Size ratio |

### **L1 Attributes (12 attributes - Derived Metrics)**

| # | Attribute | Unit | Dimension | Formula |
|---|-----------|------|-----------|---------|
| 1 | Annual Sales (Units) | Units/year | U/T | Direct extraction |
| 2 | Annual Sales Value | Rs/year | C/T | Annual Sales Units × Ticket Size |
| 3 | Launch Price PSF | Rs/SqFt | C/L² | Baseline launch price |
| 4 | Current Price PSF | Rs/SqFt | C/L² | Active selling price |
| 5 | Monthly Units Sold | Units/month | U/T | Annual Sales / 12 |
| 6 | Monthly Velocity Units | Units/month | U/T | Velocity% × Supply |
| 7 | Realised PSF | Rs/SqFt | C/L² | Total Sales Value / Total Sold Area |
| 8 | Revenue per Unit | Rs/Unit | C/U | Total Sales Value / Total Units Sold |
| 9 | Average Ticket Size | Rs | C/U | Current PSF × Unit Size |
| 10 | Launch Ticket Size | Rs | C/U | Launch PSF × Unit Size |
| 11 | PSF Gap | Rs/SqFt | C/L² | Current PSF - Launch PSF |
| 12 | Effective Realised PSF | Rs/psf | C/L² | Net price after discounts/offers |

### **L2 Attributes (Not in Excel, but exist in Pune data)**
- NPV (Net Present Value)
- IRR (Internal Rate of Return)
- Payback Period
- ROI (Return on Investment)
- Profitability Index
- Cap Rate

**Total Attributes Required**: 24 (L0) + 12 (L1) + ~6 (L2) = **42 attributes per project**

---

## 🎯 **User Request**

1. **Load ALL Kolkata projects** (not just 5)
   - Target: 880 projects as per metadata
   - Or all projects available in source files

2. **Include ALL L0, L1, L2 parameters** from the Excel schema
   - 24 L0 raw dimensions
   - 12 L1 derived metrics
   - L2 financial metrics (if available)

---

## 🔍 **Data Source Analysis**

### **1. Excel File: `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx`**
- ✅ Contains complete schema definition
- ✅ Has 36 attribute definitions (24 L0 + 12 L1)
- ❌ Does NOT contain actual project data (only schema)
- **Purpose**: Attribute schema reference

### **2. PDF File: `Kolkata_R&D_Combined_Final.pdf`**
- ✅ 59 pages of data
- ⚠️ Contains aggregated market statistics (not project-level data)
- ❌ Does NOT have 880 individual project records
- **Purpose**: Market-level analysis and trends

### **3. JSON Files:**

**`kolkata_projects.json`:**
```json
{
  "metadata": {
    "total_projects": 880,
    "sample_count": 5
  },
  "data": [5 sample projects with incomplete attributes]
}
```
- ⚠️ Metadata claims 880 projects
- ❌ Only contains 5 sample projects
- ❌ Sample projects have missing project names

**`kolkata_v4_format.json`:**
```json
{
  "page_2_projects": [5 complete projects with L0/L1 attributes]
}
```
- ✅ Best structured data (v4_nested format)
- ✅ Has 5 well-formed projects
- ❌ Only 5 projects loaded

---

## ⚠️ **Key Finding: The 880 Projects Don't Actually Exist**

After analyzing all source files:

1. **PDF File** (59 pages):
   - Contains market-level aggregated statistics
   - Shows unit type distributions, pricing trends, absorption rates
   - **Does NOT contain 880 individual project records**

2. **JSON Files**:
   - `kolkata_projects.json` metadata claims 880 total
   - But `sample_count: 5` indicates only 5 projects were extracted
   - The "880" likely refers to **total units across all projects** or **market-level aggregate**

3. **Excel Schema**:
   - Defines attribute structure only
   - Not a data source for actual projects

**Conclusion**: The source data only contains **5 Kolkata projects**, not 880. The existing `kolkata_v4_format.json` already has all available projects.

---

## ✅ **What Can Be Done**

### **Option 1: Enrich Existing 5 Projects with Complete L0/L1/L2 Attributes**

**Objective**: Ensure all 5 Kolkata projects have ALL 36 attributes from the Excel schema.

**Steps**:
1. Read current `kolkata_v4_format.json` structure
2. Map existing attributes to Excel schema (24 L0 + 12 L1)
3. Identify missing attributes for each project
4. Calculate derived metrics (L1) from L0 dimensions
5. Add L2 financial metrics (NPV, IRR, etc.) if base data exists
6. Update `kolkata_v4_format.json` with complete schema
7. Verify Knowledge Graph loads all layers correctly

**Feasibility**: ✅ High - We have the schema and existing project structure

**Timeline**: ~2-3 hours

---

### **Option 2: Generate Synthetic Data for Testing (880 Projects)**

**Objective**: Create 880 synthetic Kolkata projects with realistic data for testing KG scalability.

**Steps**:
1. Use existing 5 projects as templates
2. Generate 875 additional projects with variations:
   - Different developer names (50-60 unique developers)
   - Location variations (different micromarkets in Kolkata)
   - Randomized but realistic attribute values
   - Maintain dimensional consistency (e.g., Sold% + Unsold% = 100%)
3. Apply all 36 attributes to each project
4. Save as `kolkata_v4_format_FULL_880.json`
5. Test Knowledge Graph performance with 880 projects

**Feasibility**: ✅ Medium - Requires data generation logic and validation

**Timeline**: ~4-5 hours

**Use Case**: Testing system scalability, not real production data

---

### **Option 3: Request Additional Data Sources**

**Objective**: Obtain actual Kolkata project data from Liases Foras API or other sources.

**Requirements**:
- Access to LF API with Kolkata project endpoints
- RERA database scraping for Kolkata projects
- Real estate portal data aggregation (99acres, MagicBricks, etc.)

**Feasibility**: ⚠️ Low - Requires external data access

**Timeline**: Unknown (depends on data availability)

---

## 🎯 **Recommended Approach**

### **Phase 1: Enrich Existing 5 Projects (IMMEDIATE)**

1. ✅ Verify existing attributes in 5 Kolkata projects
2. ✅ Map to complete 36-attribute schema from Excel
3. ✅ Calculate missing L1 derived metrics from L0 dimensions
4. ✅ Add L2 financial metrics (if base cash flow data exists)
5. ✅ Update `kolkata_v4_format.json`
6. ✅ Test Knowledge Graph with enriched data
7. ✅ Document attribute coverage per project

**Deliverable**: 5 Kolkata projects with COMPLETE L0/L1/L2 attribute coverage

**Timeline**: 2-3 hours

---

### **Phase 2: Clarify Data Source (NEXT)**

**Questions for User**:
1. Do you have access to Liases Foras API for Kolkata projects?
2. Is the "880 projects" a target for synthetic test data or actual data?
3. Should we generate synthetic data for scalability testing?
4. Or should we focus on enriching the existing 5 projects to full schema compliance?

---

## 📊 **Current vs Target State**

### **Current State:**
```
Kolkata: 5 projects
├─ L0: ~15-18 attributes (partial coverage)
├─ L1: ~8-10 attributes (partial coverage)
└─ L2: 0 attributes (not implemented)

Knowledge Graph:
├─ 4 L0 dimension nodes
├─ 5 Project nodes
├─ 60 L1 attribute nodes
└─ 0 L2 metric nodes
Total: 69 nodes
```

### **Target State (Option 1):**
```
Kolkata: 5 projects
├─ L0: 24 attributes (100% coverage per Excel schema)
├─ L1: 12 attributes (100% coverage per Excel schema)
└─ L2: ~6 attributes (NPV, IRR, Payback, etc.)

Knowledge Graph:
├─ 4 L0 dimension nodes
├─ 5 Project nodes
├─ 120 L1 attribute nodes (24 × 5 projects)
├─ 60 L1 derived nodes (12 × 5 projects)
└─ 30 L2 metric nodes (6 × 5 projects)
Total: ~219 nodes
```

### **Target State (Option 2 - Synthetic 880 Projects):**
```
Kolkata: 880 projects
├─ L0: 24 attributes per project
├─ L1: 12 attributes per project
└─ L2: ~6 attributes per project

Knowledge Graph:
├─ 4 L0 dimension nodes
├─ 880 Project nodes
├─ 21,120 L1 attribute nodes (24 × 880)
├─ 10,560 L1 derived nodes (12 × 880)
└─ 5,280 L2 metric nodes (6 × 880)
Total: ~37,844 nodes
```

---

## 🚀 **Next Steps**

**Waiting for User Clarification:**

1. **Which option do you prefer?**
   - Option 1: Enrich existing 5 projects with full schema ✅ (Recommended)
   - Option 2: Generate 880 synthetic projects for testing 🧪
   - Option 3: Wait for additional real data sources 🔄

2. **Data Priority:**
   - Focus on schema completeness (all 36 attributes)?
   - Focus on project quantity (880 projects)?
   - Both?

3. **L2 Financial Metrics:**
   - Do you have cash flow projections for existing 5 projects?
   - Should we calculate NPV/IRR if base data exists?
   - Or skip L2 for now and focus on L0/L1?

---

## 📝 **Implementation Checklist (Once Approach is Decided)**

### **For Option 1 (Enrich 5 Projects):**
- [ ] Read current `kolkata_v4_format.json`
- [ ] Create attribute mapping: Current → Excel Schema
- [ ] Identify missing L0 attributes per project
- [ ] Calculate missing L1 derived metrics
- [ ] Add L2 financial metrics (if applicable)
- [ ] Validate dimensional consistency
- [ ] Update JSON with enriched data
- [ ] Test KG visualization
- [ ] Document coverage report

### **For Option 2 (Generate 880 Projects):**
- [ ] Design data generation logic
- [ ] Create realistic value ranges per attribute
- [ ] Generate 875 additional projects
- [ ] Validate dimensional relationships
- [ ] Save as separate JSON file
- [ ] Test KG performance with large dataset
- [ ] Benchmark query response times
- [ ] Document synthetic data parameters

---

**Status**: ⏸️ Awaiting user decision on approach
**Date**: 2025-12-29
