#!/bin/bash
# Quick execution script for comprehensive Kolkata enrichment

echo "=================================="
echo "Comprehensive Kolkata Enrichment"
echo "=================================="
echo ""
echo "Input:  /Users/tusharsikand/Downloads/Kolkata R&D (57 Excel files)"
echo "Output: /Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata/kolkata_v4_comprehensive.json"
echo ""
echo "Starting enrichment process..."
echo ""

cd /Users/tusharsikand/Documents/Projects/liases-foras
python3 scripts/comprehensive_kolkata_enrichment.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================="
    echo "✅ Enrichment completed successfully!"
    echo "=================================="
    echo ""
    echo "Output file details:"
    ls -lh /Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata/kolkata_v4_comprehensive.json
    echo ""
    echo "To view the output:"
    echo "  cat /Users/tusharsikand/Documents/Projects/liases-foras/data/extracted/kolkata/kolkata_v4_comprehensive.json | jq . | less"
    echo ""
else
    echo ""
    echo "=================================="
    echo "❌ Enrichment failed!"
    echo "=================================="
    echo "Check the error messages above for details."
    exit 1
fi
