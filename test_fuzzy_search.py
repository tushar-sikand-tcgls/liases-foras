"""Test fuzzy search for Project Age"""

from app.services.enriched_layers_service import get_enriched_layers_service

service = get_enriched_layers_service()

# Test exact match
print("=== EXACT MATCH TEST ===")
attr = service.get_attribute("project age months")
print(f"Looking for: 'project age months'")
print(f"Found: {attr}")

# Test exact match with parentheses
print("\n=== EXACT MATCH WITH PARENTHESES ===")
attr2 = service.get_attribute("project age (months)")
print(f"Looking for: 'project age (months)'")
print(f"Found: {attr2}")
if attr2:
    print(f"  Target: {attr2.target_attribute}")

# Test fuzzy search
print("\n=== FUZZY SEARCH TEST ===")
result = service.search_by_prompt("Project Age Months")
print(f"Searching for: 'Project Age Months'")
print(f"Result: {result}")
if result:
    attr, confidence = result
    print(f"  Found: {attr.target_attribute}")
    print(f"  Confidence: {confidence}")

# Test with other variations
print("\n=== VARIATION TESTS ===")
variations = [
    "project age",
    "age of project",
    "how old is project",
    "months since launch"
]
for var in variations:
    result = service.search_by_prompt(var)
    if result:
        attr, conf = result
        print(f"{var:30} → {attr.target_attribute} (confidence: {conf:.2f})")
    else:
        print(f"{var:30} → NOT FOUND")

# List all Layer 1 attributes with 'age' in the name
print("\n=== ALL LAYER 1 ATTRIBUTES WITH 'AGE' ===")
for attr in service.get_layer1_attributes():
    if 'age' in attr.target_attribute.lower():
        print(f"  {attr.target_attribute}")
