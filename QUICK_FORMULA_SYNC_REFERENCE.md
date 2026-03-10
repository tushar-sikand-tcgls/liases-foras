# Quick Reference: Formula Sync System

## Confirmation: 19 Calculated Attributes ✅

```
Total: 36 attributes
├── Direct Extraction: 17 attributes (from Liases Foras)
└── Calculated: 19 attributes (formulas from Excel)
```

## Quick Commands

### Check Sync Status
```bash
python3 -m app.services.formula_validator
```

**Expected Output:**
```
✅ ALL CHECKS PASSED - Excel and Calculator are in sync!
```

### Enable Auto-Validation (Dev Mode)
```bash
# In .env file or shell:
export VALIDATE_FORMULAS_ON_STARTUP=true

# Or in Python:
import os
os.environ['VALIDATE_FORMULAS_ON_STARTUP'] = 'true'
from app.services.derived_metrics_calculator import get_calculator
calculator = get_calculator()
```

### Test Calculator
```python
from app.services.derived_metrics_calculator import get_calculator

calculator = get_calculator()
print(f"Loaded {len(calculator.formulas)} formulas")  # Should be 19
```

## When Excel is Updated

1. **Edit Excel:** Update `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx`
2. **Validate:** Run `python3 -m app.services.formula_validator`
3. **Review:** Check for ⚠️ warnings
4. **Update Code:** (if needed) Add new term mappings
5. **Re-validate:** Confirm ✅ all checks pass

## Key Files

| File | Purpose |
|------|---------|
| `app/services/formula_validator.py` | Validation system |
| `app/services/derived_metrics_calculator.py` | Generic calculator |
| `FORMULA_VALIDATION_GUIDE.md` | Detailed documentation |
| `FORMULA_SYNC_SUMMARY.md` | Implementation summary |
| `/tmp/attributes_metadata.json` | Exported metadata (auto-generated) |

## 19 Calculated Attributes (Quick List)

1. Unsold Units
2. Sold Units
3. Monthly Units Sold
4. Monthly Velocity Units
5. Months of Inventory
6. Price Growth (%)
7. Realised PSF
8. Revenue per Unit
9. Unsold Inventory Value
10. Annual Absorption Rate
11. Future Sellout Time
12. Average Ticket Size
13. Launch Ticket Size
14. PSF Gap
15. Annual Clearance Rate
16. Sellout Time
17. Sellout Efficiency
18. Effective Realised PSF
19. Price-to-Size Ratio

## Troubleshooting

**Problem:** "Formula not found" errors
**Solution:** Add mapping in `derived_metrics_calculator.py`:
```python
term_mapping = {
    'YourNewTerm': 'kgFieldName',
}
```

**Problem:** Validation shows missing formulas
**Solution:** Restart calculator to reload Excel formulas

**Problem:** Formula returns None
**Solution:** Check required input data exists in KG

## Status

✅ **System Status:** Production Ready
✅ **Last Validated:** 2025-01-16
✅ **Sync Status:** Excel and Calculator in perfect sync

---
For detailed docs: See `FORMULA_VALIDATION_GUIDE.md`
