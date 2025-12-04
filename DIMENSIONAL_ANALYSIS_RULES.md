# Dimensional Analysis Rules for Real Estate Analytics

## Division Creates New Layers ✓ (PROVEN)

### Layer 0 ÷ Layer 0 → Layer 1 (Derived Metrics)

**Evidence from Physics & Real Estate:**

| Operation | Dimension | Result | Meaning | Layer |
|-----------|-----------|--------|---------|-------|
| **Price ÷ Area** | CF/L² | PSF | Price per sqft | L1 ✓ |
| **Price ÷ Units** | CF/U | ASP | Average selling price | L1 ✓ |
| **Units ÷ Time** | U/T | Velocity | Sales velocity | L1 ✓ |
| **Area ÷ Units** | L²/U | Area/Unit | Average unit size | L1 ✓ |
| **Revenue ÷ Time** | CF/T | Rate | Monthly revenue rate | L1 ✓ |

**Why division works:**
- Creates **ratios** and **rates**
- Reduces dimensional complexity
- Produces meaningful business metrics
- Well-established in physics (velocity = distance/time)

---

## Multiplication Creates New Layers? 🤔 (UNPROVEN in Real Estate)

### Analysis of Multiplication

**In Physics** (multiplication DOES create layers):
- Force = Mass × Acceleration (F = M × L/T²)
- Energy = Force × Distance (E = M×L²/T²)
- Power = Energy ÷ Time (P = M×L²/T³)

✓ Physics uses multiplication to create compound dimensions

**In Real Estate** (multiplication is questionable):

| Operation | Dimension | Result | Meaningful? | Creates Layer? |
|-----------|-----------|--------|-------------|----------------|
| Units × Area | U × L² | ??? | ❌ No business meaning | ❌ No |
| Price × Time | CF × T | ??? | ❓ Cumulative cash flow? | ❓ Maybe |
| Units × Time | U × T | ??? | ❌ No business meaning | ❌ No |
| Price × Units | CF × U | ??? | ❌ Just scaling | ❌ No |

**Analysis:**
- **CF × U = Total cost if each unit costs CF** → This is just aggregation/scaling, NOT a new dimension
- **U × L² = ???** → No meaningful business interpretation
- **CF × T = Cumulative cash flow** → MAYBE valid? But this is more like a sum over time, not a new dimension

**Conclusion:** In real estate, multiplication **rarely** creates meaningful new layers.

---

## Current Recommendation: Division-First Strategy

### Rule: Division creates layers, multiplication does not (with rare exceptions)

**Why:**
1. **Division** consistently produces meaningful metrics (PSF, ASP, Velocity)
2. **Multiplication** in real estate is usually:
   - Scaling (same dimension)
   - Aggregation (sum, not a new dimension)
   - Or physically meaningless

### Exceptions to Consider (Future):

**1. Cumulative Cash Flow (CF × T)?**
```
Monthly Cash Flow × Number of Months = Cumulative Cash Flow
Dimension: CF × T = CF·T
```
- **Question:** Is this a new dimension or just time-aggregated CF?
- **Answer:** It's still CF dimension (money), just accumulated over time
- **Verdict:** NOT a new layer, stays in Layer 0

**2. Area-Weighted Price (CF/L² × L²)?**
```
PSF × Area = Total Price
(CF/L²) × L² = CF
```
- This **cancels out** to original dimension (CF)
- **Verdict:** NOT a new layer

**3. Velocity × Time (U/T × T)?**
```
Sales Velocity × Time Period = Total Units Sold
(U/T) × T = U
```
- This **cancels out** to original dimension (U)
- **Verdict:** NOT a new layer

---

## Final Answer to Your Question

### Statement: "Division creates new layers (sometimes multiplication too)"

**Verdict:**
- **Division:** ✓ **PROVEN** - Consistently creates meaningful Layer 1 metrics
- **Multiplication:** ❌ **REJECTED** (for now) - No clear examples in real estate context

### Recommendation:

**Keep the system flexible but default to division only:**

```python
# Definite layer creators
LAYER_CREATORS = {
    'division': True,   # CF/L² → PSF (Layer 1) ✓
    'multiplication': False  # No proven examples in real estate ❌
}

# Future: If we find a valid multiplication case, add it
# Example: If "cumulative cash flow" becomes a standard metric
```

### How to Handle in Code:

```python
def detect_layer_from_operation(self, operation: str, operands: List[Dimension]) -> int:
    """
    Determine layer from operation

    RULE: Only division creates new layers (for now)
    """
    if operation == 'divide':
        # Division creates new layer
        max_layer = max(op.layer for op in operands)
        return min(max_layer + 1, 3)

    elif operation == 'multiply':
        # Multiplication does NOT create new layer (stays in same layer)
        # Exception: If we find valid examples, add conditional logic here
        return max(op.layer for op in operands)

    else:
        # Add, subtract, etc. - stay in same layer
        return max(op.layer for op in operands)
```

---

## Open Questions (For Future Research)

1. **Cumulative Cash Flow:** Is CF×T a new dimension or just aggregated CF?
2. **Composite Indices:** Could multiplication create index scores? (e.g., Developer Score = Quality × Scale)
3. **Cross-Layer Operations:** What about (L1 × L1) or (L1 × L0)?

### If You Find Examples:

If you discover real estate cases where multiplication creates meaningful new metrics, document them here:

```
Example:
Operation: ??? × ???
Result: ???
Dimension: ???
Business Meaning: ???
Layer: L?
```

Then we'll add it to the system!

---

## Summary

| Operation | Creates New Layer? | Evidence | Confidence |
|-----------|-------------------|----------|------------|
| **Division** | ✓ YES | PSF, ASP, Velocity, etc. | **High** |
| **Multiplication** | ❌ NO | No clear examples | **High** |
| **Addition** | ❌ NO | Same dimension | **High** |
| **Subtraction** | ❌ NO | Same dimension | **High** |

**Default behavior:** Division only creates layers.
**Future:** Keep code flexible to add multiplication if proven useful.
