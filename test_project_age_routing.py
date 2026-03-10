"""Debug script to test Project Age routing"""

from app.services.enriched_layers_service import get_enriched_layers_service
from app.services.prompt_router import prompt_router

# Get the enriched layers service
service = get_enriched_layers_service()

# Check if Project Age attribute exists
attr = service.get_attribute("project age (months)")
print(f"\n=== ATTRIBUTE LOOKUP ===")
print(f"Searching for: 'project age (months)'")
print(f"Found: {attr}")
if attr:
    print(f"  - Target Attribute: {attr.target_attribute}")
    print(f"  - Layer: {attr.layer}")
    print(f"  - Requires Calculation: {attr.requires_calculation}")
    print(f"  - Formula: {attr.formula_derivation}")
else:
    # Try other variations
    print(f"\nTrying other variations...")
    all_attrs = service.get_all_attributes()
    for a in all_attrs:
        if 'age' in a.target_attribute.lower():
            print(f"  Found: {a.target_attribute} (Layer: {a.layer})")

# Check generated patterns
print(f"\n=== GENERATED PATTERNS ===")
patterns = service.generate_capability_patterns()
print(f"Total patterns generated: {len(patterns)}")

for cap_name, cap_config in patterns.items():
    if 'age' in cap_name.lower():
        print(f"\nCapability: {cap_name}")
        print(f"  Keywords: {cap_config['keywords']}")
        print(f"  Patterns: {cap_config['patterns']}")
        print(f"  Layer: {cap_config['layer']}")

# Test prompt routing
print(f"\n=== PROMPT ROUTING TEST ===")
test_query = "What is project age of Sara city?"
print(f"Query: '{test_query}'")
route_decision = prompt_router.analyze_prompt(test_query)
print(f"  Layer: {route_decision.layer}")
print(f"  Capability: {route_decision.capability}")
print(f"  Confidence: {route_decision.confidence}")

# Test variations
test_queries = [
    "What is project age of Sara city?",
    "project age for sara city",
    "how many months since launch",
    "age of project",
    "calculate project age"
]

print(f"\n=== TESTING MULTIPLE VARIATIONS ===")
for query in test_queries:
    route = prompt_router.analyze_prompt(query)
    print(f"{query:40} → Layer: {route.layer}, Capability: {route.capability}, Confidence: {route.confidence:.2f}")
