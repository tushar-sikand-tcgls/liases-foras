# Formula Validation System

## Overview

The formula validation system ensures that the Excel file containing attribute definitions stays in sync with the calculator implementation. This prevents issues where formulas are updated in Excel but not reflected in the code.

## Summary of Attributes

From `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx`:

- **Total Attributes:** 36
  - **Direct Extraction:** 17 attributes (sourced directly from Liases Foras)
  - **Calculated:** 19 attributes (derived using formulas)

## Validation Tool

### Location
`/Users/tusharsikand/Documents/Projects/liases-foras/app/services/formula_validator.py`

### What It Checks

1. ✅ **Missing in Calculator:** Formulas in Excel but not implemented
2. ✅ **Extra in Calculator:** Formulas in code but not in Excel
3. ✅ **Formula Changes:** Differences between Excel and implementation
4. ✅ **Count Validation:** Total formula count matches (should be 19)

### When to Run

**ALWAYS run the validator after:**
- Updating the Excel file with new formulas
- Modifying existing formulas in Excel
- Adding or removing calculated attributes
- Before deploying to production

## Usage

### Manual Validation

```bash
# Run standalone validation
python3 -m app.services.formula_validator

# Or using the run_validation function
python3 -c "from app.services.formula_validator import run_validation; run_validation()"
```

### Automatic Validation on Startup (Dev Mode)

Set environment variable to enable automatic validation:

```bash
# In .env file
VALIDATE_FORMULAS_ON_STARTUP=true

# Or export in shell
export VALIDATE_FORMULAS_ON_STARTUP=true
```

The calculator will automatically check formula sync status on initialization.

### Programmatic Validation

```python
from app.services.formula_validator import FormulaValidator

validator = FormulaValidator(
    excel_path="/path/to/LF-Layers_FULLY_ENRICHED_ALL_36.xlsx"
)

# Print full validation report
passed = validator.print_validation_report()

# Or get results programmatically
validator.load_excel_metadata()
results = validator.validate_against_calculator()

if results['missing_in_calculator']:
    print("Missing formulas:", results['missing_in_calculator'])
```

## Output Examples

### ✅ All Checks Passed

```
================================================================================
FORMULA VALIDATION REPORT
================================================================================
✅ Loaded Excel metadata:
   - Direct extraction: 17 attributes
   - Calculated: 19 attributes
   - Total: 36 attributes
✅ Loaded 19 calculated formulas from Excel

📊 SUMMARY:
   - Excel has 19 calculated formulas
   - Calculator loaded 19 formulas

✅ ALL CHECKS PASSED - Excel and Calculator are in sync!
================================================================================
```

### ⚠️ Sync Issues Detected

```
================================================================================
FORMULA VALIDATION REPORT
================================================================================
...

⚠️  MISSING IN CALCULATOR (2):
   - New Metric XYZ: formula definition
   - Another New Metric: formula definition

⚠️  FORMULA CHANGES (1):
   - PSF Gap: Excel='CurrentPSF-LaunchPSF' vs Calc='LaunchPSF-CurrentPSF'

❌ SYNC ISSUES DETECTED - Please review and update calculator!
================================================================================
```

## Workflow When Excel is Updated

### 1. Update Excel File
Edit `LF-Layers_FULLY_ENRICHED_ALL_36.xlsx` with new formulas or changes.

### 2. Run Validation
```bash
python3 -m app.services.formula_validator
```

### 3. Review Results
If issues are detected, the validator will show:
- Which formulas are missing in the calculator
- Which formulas have changed
- Which formulas are extra (in code but not Excel)

### 4. Update Code (if needed)

The calculator is **generic** and reads formulas from Excel dynamically, so:

✅ **No code changes needed for:**
- Adding new calculated attributes (as long as they use existing field names)
- Changing formula logic (e.g., `CurrentPSF - LaunchPSF` → `LaunchPSF - CurrentPSF`)
- Removing calculated attributes

❌ **Code changes needed for:**
- New field names in formulas that don't exist in KG data
- New mathematical operations not supported by the term mapping

### 5. Update Term Mapping (if needed)

If new formulas use new shorthand terms, update the `term_mapping` in `derived_metrics_calculator.py`:

```python
term_mapping = {
    'Supply': 'totalSupplyUnits',
    'Annual Sales': 'annualSalesUnits',
    # Add new mappings here
    'NewTerm': 'newFieldNameInKG',
}
```

### 6. Re-validate
Run the validator again to confirm all issues are resolved.

### 7. Test Calculated Metrics
```bash
# Test with sample project data
python3 -c "
from app.services.derived_metrics_calculator import get_calculator

calculator = get_calculator()
sample_data = {
    'totalSupplyUnits': 770,
    'soldPercent': 40,
    'unsoldPercent': 60,
    'launchPricePSF': 2000,
    'currentPricePSF': 2200
}

results = calculator.calculate_all(sample_data)
print('Calculated Metrics:')
for key, value in results.items():
    print(f'  {key}: {value:.2f}')
"
```

## 19 Calculated Attributes (Current)

As of the last validation, these 19 attributes are calculated:

1. **Unsold Units** - `Supply × Unsold%`
2. **Sold Units** - `Supply × Sold%`
3. **Monthly Units Sold** - `Annual Sales / 12`
4. **Monthly Velocity Units** - `Velocity% × Supply`
5. **Months of Inventory** - `Unsold / Monthly Units Sold`
6. **Price Growth (%)** - `(Current−Launch) / Launch`
7. **Realised PSF** - `(Value × 1e7) / (Units × Size)`
8. **Revenue per Unit** - `(Value × 1e7) / Units`
9. **Unsold Inventory Value** - `Units × Size × PSF / 1e7`
10. **Annual Absorption Rate** - `Annual Sales / Supply`
11. **Future Sellout Time** - `Unsold / Annual Sales`
12. **Average Ticket Size** - `Unit Size × CurrentPSF`
13. **Launch Ticket Size** - `Unit Size × LaunchPSF`
14. **PSF Gap** - `CurrentPSF−LaunchPSF`
15. **Annual Clearance Rate** - `Annual Sales / Supply`
16. **Sellout Time** - `Supply / Annual Sales`
17. **Sellout Efficiency** - `(AnnualSales × 12) / Supply`
18. **Effective Realised PSF** - `(Value × 1e7) / (Units × Size)`
19. **Price-to-Size Ratio** - `CurrentPSF / Size`

## Metadata Export

The validator also exports complete attribute metadata to JSON:

```bash
python3 -m app.services.formula_validator
# Exports to: /tmp/attributes_metadata.json
```

This JSON file contains:
- All 17 direct extraction attributes with descriptions
- All 19 calculated attributes with formulas and descriptions
- Complete metadata (units, dimensions, layers)

Use this metadata for:
- Embedding in LLM prompts (for showing definitions)
- Documentation generation
- API schema validation

## Best Practices

1. **Always validate after Excel updates** - Run the validator immediately after editing the Excel file

2. **Enable validation in dev mode** - Set `VALIDATE_FORMULAS_ON_STARTUP=true` during development

3. **Check before commits** - Run validation before committing Excel file changes

4. **Document formula changes** - When changing formulas, document the reason in commit messages

5. **Test calculated values** - After formula changes, test with sample data to verify correctness

## Troubleshooting

### "Formula not found" errors

**Cause:** The term used in the formula doesn't match any field in the knowledge graph.

**Fix:** Add a mapping in `derived_metrics_calculator.py`:
```python
term_mapping = {
    'YourTerm': 'actualKGFieldName',
}
```

### "Validation shows missing formulas"

**Cause:** Excel has new calculated attributes that the calculator hasn't loaded.

**Fix:** Restart the calculator to reload formulas, or check if Excel file path is correct.

### "Formula evaluation returns None"

**Cause:** Required input data is missing from the project data.

**Fix:** Check that all fields referenced in the formula exist in the KG data.

## Integration with CI/CD (Future)

Add to your CI/CD pipeline:

```yaml
# .github/workflows/validate.yml
- name: Validate Formulas
  run: |
    python3 -m app.services.formula_validator
    if [ $? -ne 0 ]; then
      echo "Formula validation failed!"
      exit 1
    fi
```

This ensures formulas stay in sync across deployments.

## Summary

✅ **Confirmed:** 19 calculated attributes in Excel
✅ **Validator created:** Automatic sync checking
✅ **Integration added:** Auto-validate on startup (optional)
✅ **Metadata export:** JSON generation for LLM prompts

**Next time the Excel file is updated, just run:**
```bash
python3 -m app.services.formula_validator
```
