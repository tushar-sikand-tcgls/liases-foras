#!/usr/bin/env python3
"""Test average query display issue"""

from app.services.simple_query_handler import SimpleQueryHandler
from app.services.data_service import DataServiceV4

data_service = DataServiceV4()
handler = SimpleQueryHandler(data_service)

# Test the average query
result = handler.handle_query('What is the average project size')

print('Query: "What is the average project size"')
print('=' * 60)
print(f'Status: {result.status}')
print(f'Operation: {result.operation}')
print(f'Result: {result.result}')
print()
print('Calculation:')
for key, value in result.calculation.items():
    if key != 'breakdown':
        print(f'  {key}: {value}')
