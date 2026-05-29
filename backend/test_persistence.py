#!/usr/bin/env python
"""
🧪 TEST DATA PERSISTENCE via API
=================================
This script tests if the backend properly stores health data.
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5000/api'

# Test user credentials (from database)
TEST_MOBILE = '9876543210'
TEST_PASSWORD = 'test@123'

print("\n" + "="*70)
print("🧪 TESTING DATA PERSISTENCE VIA API")
print("="*70)

# 1. LOGIN
print("\n1️⃣ LOGIN")
print("-" * 70)
login_resp = requests.post(f'{BASE_URL}/auth/login', json={
    'mobile': TEST_MOBILE,
    'password': TEST_PASSWORD
})
print(f"Status: {login_resp.status_code}")

if login_resp.status_code == 200:
    data = login_resp.json()
    access_token = data['data']['access_token']
    refresh_token = data['data'].get('refresh_token', '')
    print(f"✅ Login successful")
    print(f"   Access Token: {access_token[:30]}...")
    print(f"   Refresh Token: {refresh_token[:30] if refresh_token else '(none)'}...")
else:
    print(f"❌ Login failed: {login_resp.text}")
    exit(1)

headers = {'Authorization': f'Bearer {access_token}'}

# 2. LIST FAMILIES
print("\n2️⃣ LIST EXISTING FAMILIES")
print("-" * 70)
families_resp = requests.get(f'{BASE_URL}/families/', headers=headers)
print(f"Status: {families_resp.status_code}")
if families_resp.status_code == 200:
    families = families_resp.json()['data']
    print(f"✅ Found {len(families)} families")
    if families:
        family_id = families[0]['id']
        print(f"   First family ID: {family_id}")
else:
    print(f"❌ Failed to list families: {families_resp.text}")
    exit(1)

# 3. CREATE A VISIT RECORD
print("\n3️⃣ CREATE VISIT RECORD")
print("-" * 70)
visit_data = {
    'beneficiary_name': 'Test Beneficiary',
    'asha_id': 'ASH001',
    'visit_date': '2026-05-29',
    'visit_type': 'general',
    'status': 'completed',
    'notes': 'Test visit from API'
}
print(f"Sending: {json.dumps(visit_data, indent=2)}")
visit_resp = requests.post(f'{BASE_URL}/visits/', headers=headers, json=visit_data)
print(f"Status: {visit_resp.status_code}")
print(f"Response: {visit_resp.text[:300]}")

if visit_resp.status_code in [200, 201]:
    print("✅ Visit created successfully")
    try:
        visit_id = visit_resp.json()['data']['id']
    except:
        visit_id = None
else:
    print(f"❌ Failed to create visit")

# 4. QUERY DATABASE DIRECTLY
print("\n4️⃣ CHECK DATABASE FOR NEW RECORDS")
print("-" * 70)
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
ctx = app.app_context()
ctx.push()

with db.engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM visit_records'))
    visit_count = result.scalar()
    print(f"Visit records in DB: {visit_count}")
    
    result = conn.execute(text('SELECT COUNT(*) FROM families'))
    family_count = result.scalar()
    print(f"Families in DB: {family_count}")

print("\n" + "="*70)
