#!/usr/bin/env python3
"""
Full end-to-end test with complete logging.
"""
import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

BASE_URL = 'http://localhost:5000/api'

print("\n" + "="*80)
print("COMPREHENSIVE DATA PERSISTENCE TEST")
print("="*80)

# Step 1: Login
print("\n[1] LOGIN")
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'mobile': '9876543210',
    'password': 'test@123'
})
print(f"    Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"    Error: {resp.text}")
    exit(1)

token = resp.json()['data']['access_token']
print(f"    Token: {token[:20]}...")

# Step 2: Get DB count BEFORE
print("\n[2] DATABASE COUNT BEFORE")
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
    count_before = result.scalar()
    print(f"    Records: {count_before}")

# Step 3: Create visit
print("\n[3] CREATE VISIT - Flutter payload with extra fields")
headers = {'Authorization': f'Bearer {token}'}
payload = {
    'patient_name': 'John Doe',  # Flutter field name
    'village': 'Test Village',  # Not in schema
    'phone': '9876543210',  # Not in schema
    'reason': 'general',  # Different field name
    'notes': 'Test record',
    'asha_id': 'ASH001',
    'status': 'pending',
    'visit_date': datetime.now().isoformat(),
}

print(f"    Payload: {json.dumps(payload, indent=6)}")

resp = requests.post(f'{BASE_URL}/visits/', headers=headers, json=payload)
print(f"    Response Status: {resp.status_code}")
print(f"    Response: {resp.text[:400]}")

if resp.status_code != 201:
    print("    ❌ API REJECTED REQUEST")
    exit(1)

print("    ✅ API ACCEPTED REQUEST")

# Step 4: Get DB count AFTER
print("\n[4] DATABASE COUNT AFTER")
with app.app_context():
    result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
    count_after = result.scalar()
    print(f"    Records: {count_after}")
    
    if count_after > count_before:
        print(f"    ✅ Record persisted! (+{count_after - count_before})")
        
        # Show the record
        result = db.session.execute(db.text('''
            SELECT id, beneficiary_name, visit_type, status, created_at 
            FROM visit_records 
            ORDER BY created_at DESC 
            LIMIT 10
        '''))
        row = result.first()
        print(f"    Record: {row[1]} ({row[2]}) - {row[3]} - {row[4]}")
    else:
        print(f"    ❌ API ACCEPTED BUT NO RECORD IN DATABASE!")
        print("    This means the transaction wasn't committed")

print("\n" + "="*80)
