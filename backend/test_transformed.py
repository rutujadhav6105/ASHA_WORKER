#!/usr/bin/env python3
"""Test with correctly transformed payload."""
import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000/api'

# Login
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'mobile': '9876543210',
    'password': 'test@123'
})
token = resp.json()['data']['access_token']

# Correctly transformed payload (as visit_service should transform it)
headers = {'Authorization': f'Bearer {token}'}
transformed_payload = {
    'beneficiary_name': 'John Doe',  # Mapped from patient_name
    'asha_id': 'ASH001',
    'village': 'Test Village',  # Extra field (should be ignored)
    'notes': 'Test record',
    'visit_type': 'general',  # Normalized from reason
    'visit_date': datetime.now().strftime('%Y-%m-%d'),  # Formatted
    'status': 'scheduled',  # Mapped from pending
}

print('Testing TRANSFORMED payload:')
print(json.dumps(transformed_payload, indent=2))

from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
    count_before = result.scalar()

resp = requests.post(f'{BASE_URL}/visits/', headers=headers, json=transformed_payload)
print(f'\nResponse Status: {resp.status_code}')

if resp.status_code in [200, 201]:
    print('✅ API ACCEPTED')
    
    with app.app_context():
        result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
        count_after = result.scalar()
        
        if count_after > count_before:
            print(f'✅ STORED IN DB (+{count_after - count_before})')
        else:
            print('❌ Not in database')
else:
    print('❌ API REJECTED:', resp.text[:300])
