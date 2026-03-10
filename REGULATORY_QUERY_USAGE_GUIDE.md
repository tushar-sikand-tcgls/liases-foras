# Regulatory Query Usage Guide

## How to Query Building Codes and Regulations

Your ATLAS Hybrid Router can now answer questions about building codes, construction rules, and regulations using the National Building Code (NBC) and UDCPR documents.

---

## Quick Start

### Supported Topics

**Development Control & Planning Regulations (DCPR/UDCPR):**
- Parking requirements for different building types
- FSI/FAR regulations and calculations
- Zoning regulations
- Development control rules
- Building height restrictions
- Setback and margin requirements
- Amenity space requirements

**National Building Code (NBC):**
- Fire safety requirements for high-rise buildings
- Structural safety codes
- Accessibility standards for differently-abled persons
- Electrical and plumbing codes
- Lift and escalator requirements
- Ventilation and lighting standards

**RERA (Real Estate Regulatory Authority):**
- Project registration requirements
- Developer compliance standards
- Carpet area definitions
- Buyer protection regulations

---

## Example Queries

### Parking Requirements
```
Query: "What are the parking requirements as per DCPR?"
Query: "How many car parking spaces are required for a 100-unit residential building?"
Query: "What is the parking requirement for commercial buildings per DCPR?"
```

**Sample Answer:**
```
The DCPR outlines specific requirements for off-street parking...

Residential Buildings:
• For every tenement with carpet area of 150 sq.m. and above:
  1 car and 1 scooter parking space
• For every tenement with carpet area 80-150 sq.m.:
  1 car and 1 scooter parking space
...

[Answer includes hyperlinks to DCPR, parking standards, regulations]
```

---

### Fire Safety Requirements
```
Query: "What are the fire safety requirements for high-rise buildings as per NBC?"
Query: "What are the fire lift requirements for buildings over 15 meters?"
Query: "What is the fire escape chute requirement for buildings?"
```

**Sample Answer:**
```
The National Building Code outlines several critical fire safety requirements:

• Fire Lifts: Buildings with height ≥15m must have fire lifts
• Fire Escape Chutes: Buildings >70m require fire escape chute shafts
• Refuge Areas: Buildings >24m must have refuge areas (15 sq.m minimum)
...

[Answer includes hyperlinks to NBC, BIS, fire safety codes]
```

---

### FSI/FAR Regulations
```
Query: "What are the RERA regulations for FSI compliance?"
Query: "How is FSI calculated as per UDCPR?"
Query: "What is the permissible FSI for residential buildings?"
```

**Sample Answer:**
```
RERA mandates developers adhere to FSI/FAR regulations set by local planning authorities...

FSI Calculation:
• Net plot area = Total area - amenity space - development plan areas
• Incentive FSI available for urban renewal projects
• Additional FSI may be granted near Metro Rail infrastructure
...

[Answer includes hyperlinks to RERA, FSI, FAR, UDCPR]
```

---

### Building Height Restrictions
```
Query: "What is the maximum building height allowed as per NBC?"
Query: "Are there height restrictions near airports?"
Query: "What are the height limits for different occupancy types?"
```

---

### Accessibility Standards
```
Query: "What are the accessibility standards for differently-abled persons?"
Query: "What are the ramp requirements as per NBC?"
Query: "What are the lift requirements for accessible buildings?"
```

---

## Hyperlinks in Answers

All answers automatically include clickable hyperlinks to authoritative sources:

### Government & Regulatory Links
- **RERA** → https://rera.maharashtra.gov.in/
- **UDCPR** → https://udcpr.maharashtra.gov.in/
- **NBC** → https://www.bis.gov.in/national-building-code/
- **BIS** → https://www.bis.gov.in/
- **PMC** → https://www.pmc.gov.in/
- **Smart Cities Mission** → https://smartcities.gov.in/
- **MoHUA** → https://mohua.gov.in/

### Real Estate Terms (Wikipedia)
- **FSI/FAR** → Floor Area Ratio
- **Carpet Area** → Carpet area definition
- **IRR** → Internal Rate of Return
- **ROI** → Return on Investment
- **Absorption Rate** → Real estate absorption
- **Cap Rate** → Capitalization rate

### Locations (Wikipedia)
- **Pune**, **Mumbai**, **Chakan**, **Maharashtra**, **India**

All links open in new tabs for easy reference while reading the answer.

---

## Query Detection

The system automatically detects regulatory queries based on keywords:

**Regulatory Keywords:**
- `dcpr`, `udcpr`, `national building code`, `nbc`, `rera`
- `building code`, `parking requirement`, `construction rule`
- `fsi regulation`, `floor space index regulation`, `zoning`
- `building regulation`, `development control`, `planning regulation`
- `fire safety code`, `accessibility standard`, `structural code`

**Routing:**
- Regulatory queries → **File Search** (NBC + UDCPR documents)
- Project/market data queries → **Knowledge Graph** (Liases Foras data)

---

## Performance Expectations

### Regulatory Queries (File Search)
- **Execution Time:** 10-15 seconds
- **Detail Level:** Comprehensive with citations
- **Source:** NBC and UDCPR PDF documents

### Project Data Queries (Knowledge Graph)
- **Execution Time:** <2 seconds
- **Detail Level:** Precise with calculations
- **Source:** Liases Foras database

---

## Tips for Best Results

1. **Be Specific:**
   - ✅ "What are parking requirements for residential buildings as per DCPR?"
   - ❌ "Tell me about parking"

2. **Mention the Regulation:**
   - Include "NBC", "DCPR", "UDCPR", "RERA" in your query
   - This ensures the system routes to the right source

3. **Ask for Specific Building Types:**
   - Residential, commercial, educational, industrial, etc.
   - This helps the system find the relevant section in the documents

4. **Combine Queries When Needed:**
   - ✅ "What are the fire safety and parking requirements for a high-rise residential building?"
   - This gets you comprehensive information in one answer

---

## Common Use Cases

### For Developers
```
"What are the RERA registration requirements for a new project?"
"What FSI is permissible for residential projects in Pune?"
"What are the parking requirements for my 200-unit project?"
```

### For Architects
```
"What are the fire escape requirements for a 25-floor building?"
"What are the setback requirements as per UDCPR?"
"What are the lift requirements for high-rise buildings?"
```

### For Compliance Officers
```
"What are the differently-abled accessibility standards?"
"What are the amenity space requirements for residential buildings?"
"What are the structural safety codes for high-rise buildings?"
```

### For Real Estate Consultants
```
"What is the FSI calculation method as per DCPR?"
"What are the parking norms for commercial buildings?"
"What are the RERA compliance requirements for developers?"
```

---

## API Endpoint

**URL:** `http://localhost:8011/api/atlas/hybrid/query`

**Request:**
```json
{
  "question": "What are the parking requirements as per DCPR?"
}
```

**Response:**
```json
{
  "status": "success",
  "answer": "The Development Control Promotion Regulations (DCPR) outline specific requirements... [with hyperlinks]",
  "execution_time_ms": 10857.14,
  "query_intent": "qualitative",
  "execution_path": "interactions_api",
  "tool_used": "file_search",
  "metadata": {
    "components": [
      "Interactions API V2",
      "File Search (managed RAG - NBC + UDCPR)",
      "Knowledge Graph (function calling)"
    ]
  }
}
```

---

## Troubleshooting

### Query Not Returning Regulatory Information
- **Check:** Does your query include regulatory keywords? (NBC, DCPR, UDCPR, RERA)
- **Solution:** Rephrase query to explicitly mention the regulation

### Answer Too Generic
- **Check:** Are you being specific about building type and requirement?
- **Solution:** Add more context (e.g., "residential buildings", "high-rise", "commercial")

### Slow Response Time (>15 seconds)
- **Cause:** File Search queries take 10-15 seconds for comprehensive answers
- **This is normal:** Regulatory deep-dive queries require searching through large PDF documents

---

## Future Enhancements

Coming soon:
- ✨ Combined queries (File Search + Knowledge Graph)
  - Example: "Calculate parking required for Sara City per DCPR"
- 📄 Citation with page numbers and section references
- 📚 Additional regulatory documents (RERA Act 2016, Land Revenue Code)
- 🔍 Smart query understanding (auto-detect regulation from context)

---

## Support

For questions or issues:
- Check backend logs: `tail -f backend.log`
- Look for `[REGULATORY-QUERY]` routing messages
- Verify File Search store is configured: `FILE_SEARCH_STORE_NAME` env variable

Backend Status:
- Port: 8011
- Regulatory routing: ✅ Active
- Reference links: ✅ Active
- File Search documents: NBC (2.12 MB) + UDCPR (5.05 MB)
