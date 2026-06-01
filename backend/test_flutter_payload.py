#!/usr/bin/env python3
"""Test Flutter-style payload with fixed schema."""
import requests
import json

# Get token
resp = requests.post('http://localhost:5000/api/auth/login', json={
    'mobile': '9876543210',
    'password': 'test@123'
})
token = resp.json()['data']['access_token']

# Test with Flutter-style payload
headers = {'Authorization': f'Bearer {token}'}
flutter_payload = {
    'beneficiary_name': 'Flutter User Test',
    'asha_id': 'ASH001',
    'village': 'Test Village',  # Flutter sends this
    'visit_type': 'general',
    'visit_date': '2026-05-31',
    'status': 'completed',
    'notes': 'Flutter app test'
}

print('Testing Flutter payload...')
print('Payload:', json.dumps(flutter_payload, indent=2))

resp = requests.post('http://localhost:5000/api/visits/', headers=headers, json=flutter_payload)
print(f'\nStatus: {resp.status_code}')

if resp.status_code in [200, 201]:
    print('✅ SUCCESS')
else:
    print('❌ FAILED:', resp.text[:300])
