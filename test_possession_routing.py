"""Test routing for Time to Possession query"""

from app.services.prompt_router import PromptRouter

router = PromptRouter()

# Test the problematic query
query = "How many months until possession for Sara city?"
print(f"Testing query: '{query}'")
print("=" * 60)

route = router.analyze_prompt(query)
print(f"Layer: {route.layer}")
print(f"Capability: {route.capability}")
print(f"Confidence: {route.confidence}")
print()

# Test alternate phrasing
alternate_queries = [
    "months until possession",
    "time to possession",
    "when is possession date",
    "how long until possession"
]

print("Testing alternate phrasings:")
print("=" * 60)
for q in alternate_queries:
    route = router.analyze_prompt(q)
    print(f"Query: '{q}'")
    print(f"  → {route.layer.name} | {route.capability} (conf: {route.confidence:.2f})")
    print()
