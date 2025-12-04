# Collapsible Calculation Details Update

## Status: ✅ COMPLETE

**Date:** 2025-12-02

---

## What Changed

The **Calculation Details** section (formula, project count, total sum) is now housed in a **default-collapsed collapsible** section, keeping the main answer clean and upfront while providing details on-demand.

---

## Before vs After

### Before (Always Visible)
```
The average across all projects is **256.7 Units**.

### Calculation Details

**Formula:** `X = Σ U / 10`
**Number of projects analyzed:** 10
**Total sum:** 2567

*Source: Liases Foras*
```

**Issue:** Details always visible, cluttering the main answer

---

### After (Collapsible by Default)
```
The average across all projects is **256.7 Units**.

[▶ Show calculation details]  ← Click to expand

*Source: Liases Foras*
```

**When Expanded:**
```
The average across all projects is **256.7 Units**.

[▼ Show calculation details]

**Formula:** `X = Σ U / 10`

**Number of projects analyzed:** 10
**Total sum:** 2567

*Source: Liases Foras*
```

**Benefits:**
- ✅ Main answer is prominent and uncluttered
- ✅ Details available on-demand (click to expand)
- ✅ Default collapsed (like a side-car)
- ✅ Native HTML `<details>` tag (clean, accessible)

---

## Implementation

### File: `frontend/components/answer_transformer.py`

**Lines 97-124 (Updated):**

```python
# OPTIONAL: Calculation Details (Collapsible by default)
if calculation:
    output_lines.append("")  # Blank line

    # Start collapsible section (HTML details tag)
    output_lines.append('<details>')
    output_lines.append('<summary><strong>Show calculation details</strong></summary>')
    output_lines.append("")  # Blank line for spacing

    formula = calculation.get('formula')
    if formula:
        output_lines.append(f"**Formula:** `{formula}`")
        output_lines.append("")

    project_count = calculation.get('projectCount')
    total = calculation.get('total')

    if project_count:
        output_lines.append(f"**Number of projects analyzed:** {project_count}")

    if total is not None:
        output_lines.append(f"**Total sum:** {total}")

    output_lines.append("")  # Blank line before closing
    output_lines.append('</details>')  # End collapsible section
```

### File: `frontend/streamlit_app.py`

**Line 830 (Updated):**

```python
# Enable HTML rendering for collapsible details
st.markdown(text_output, unsafe_allow_html=True)
```

---

## How It Works

### HTML `<details>` Tag

The collapsible is created using native HTML:

```html
<details>
  <summary><strong>Show calculation details</strong></summary>

  **Formula:** `X = Σ U / 10`

  **Number of projects analyzed:** 10
  **Total sum:** 2567

</details>
```

**Properties:**
- **Default state:** Collapsed (user must click to expand)
- **Accessibility:** Native HTML element, screen-reader friendly
- **Styling:** Browser default (arrow indicator + summary text)
- **No JavaScript:** Pure HTML/CSS, works everywhere

---

## Display Structure

### GPT-Style Answer Format

```
┌─────────────────────────────────────────────────┐
│ MAIN ANSWER (Always Visible)                    │
│ The average across all projects is 256.7 Units. │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ [▶ Show calculation details] ← Collapsed        │
│                                                  │
│ (Click to expand and see formula, count, total) │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ DATA SOURCE (Minimal Footer)                    │
│ *Source: Liases Foras*                          │
└─────────────────────────────────────────────────┘
```

---

## Test Results

### Test: Single Answer Query ✅

**Query:** "Calculate the average of all project sizes"

**Output:**
```html
The average across all projects is **256.7 Units**.

<details>
<summary><strong>Show calculation details</strong></summary>

**Formula:** `X = Σ U / 10`

**Number of projects analyzed:** 10
**Total sum:** 2567

</details>

*Source: Liases Foras*
```

**Verification:**
- ✅ Has `<details>` tag
- ✅ Has `<summary>` tag with clickable text
- ✅ Formula/count/total inside `<details>`
- ✅ Closing `</details>` tag present
- ✅ Main answer is outside (always visible)

---

## User Experience

### Desktop/Browser View

**Default (Collapsed):**
```
The average across all projects is 256.7 Units.

▶ Show calculation details

Source: Liases Foras
```

**Expanded (After Click):**
```
The average across all projects is 256.7 Units.

▼ Show calculation details
    Formula: X = Σ U / 10
    Number of projects analyzed: 10
    Total sum: 2567

Source: Liases Foras
```

### Mobile View

Same behavior, but with mobile-friendly collapsible (native browser support).

---

## Comparison: Answer Types

### Single Answer (Collapsible Details)
```
The average across all projects is **256.7 Units**.

[▶ Show calculation details]

*Source: Liases Foras*
```

### Multiple Rows (No Collapsible)
```
Here are the top 5 results:

1. **Sara City** - 1109
2. **Sara Nilaay** - 298
3. **Sara Abhiruchi Tower** - 280
4. **Pradnyesh Shriniwas** - 278
5. **The Urbana** - 168

*Source: Liases Foras*
```

**Note:** Multiple row queries typically don't have calculation details, so no collapsible is added.

---

## Benefits

### 1. Clean Answer Upfront
- Users see the result immediately
- No clutter from formulas/counts
- GPT-style clean presentation

### 2. Details on Demand
- Power users can expand to see methodology
- Casual users can ignore
- Transparency without overwhelming

### 3. Native HTML
- No custom JavaScript
- Works in all browsers
- Accessible (keyboard navigation, screen readers)

### 4. Minimal Code
- Simple HTML tags
- No complex state management
- Easy to maintain

---

## Files Modified

1. **`frontend/components/answer_transformer.py`**
   - Lines 97-124: Wrapped calculation details in `<details>` tag

2. **`frontend/streamlit_app.py`**
   - Line 830: Added `unsafe_allow_html=True` to `st.markdown()`

---

## How to Test

### In Browser

1. **Open:** http://localhost:8501

2. **Select a location** and ask:
   - "Calculate the average of all project sizes"

3. **Observe:**
   - Main answer is visible: "The average across all projects is **256.7 Units**."
   - Collapsible arrow appears: **▶ Show calculation details**
   - Default state: **Collapsed** ✓

4. **Click the arrow:**
   - Details expand
   - Shows: Formula, project count, total sum
   - Arrow changes to **▼**

5. **Click again:**
   - Details collapse
   - Arrow changes back to **▶**

---

## Summary

✅ **Calculation details now collapsible by default**
✅ **Main answer clean and upfront**
✅ **Details available on-demand (click to expand)**
✅ **Uses native HTML `<details>` tag**
✅ **No clutter, GPT-style presentation**

The side-car information (formula, methodology, counts) is now housed in a collapsible that doesn't distract from the main answer. Users get the best of both worlds:
- Quick answer for casual queries
- Deep details for power users who want to understand the calculation

**Status:** ✅ READY TO TEST
