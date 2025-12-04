#!/usr/bin/env python3
"""Test script to verify sample question routing"""

from app.services.semantic_query_matcher import SemanticQueryMatcher

matcher = SemanticQueryMatcher()

# Test all 6 sample questions
test_queries = [
    ('What is the project size of Sara City?', 'get_specific_project'),
    ('How many total units in Sara City', 'get_specific_project'),
    ('Show me Sara City project data', 'get_specific_project'),
    ('What is the average project size', 'calculate_average_project_size'),
    ('What is the total project size', 'calculate_total'),
    ('Find the standard deviation in project size', 'calculate_standard_deviation')
]

print('Sample Question Routing Verification:')
print('=' * 70)

all_pass = True
for query, expected_handler in test_queries:
    match = matcher.best_match(query)
    if match:
        actual_handler = match['handler']
        similarity = match['similarity']
        if actual_handler == expected_handler:
            status = 'PASS'
        else:
            status = 'FAIL'
            all_pass = False
        print(f'{status} | Query: "{query}"')
        print(f'      Expected: {expected_handler}')
        print(f'      Got: {actual_handler} (similarity: {similarity:.2f})')
    else:
        print(f'FAIL | Query: "{query}"')
        print(f'      Expected: {expected_handler}')
        print(f'      Got: No match')
        all_pass = False
    print()

print('=' * 70)
if all_pass:
    print('✅ ALL SAMPLE QUESTIONS ROUTE CORRECTLY')
else:
    print('❌ SOME SAMPLE QUESTIONS FAILED ROUTING')
