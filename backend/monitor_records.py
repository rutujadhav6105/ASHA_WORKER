#!/usr/bin/env python3
"""
Monitor record creation and persistence in real-time.
"""
import json
import requests
from datetime import datetime
from app import create_app
from app.extensions import db

BASE_URL = 'http://localhost:5000/api'

def check_db_records():
    """Check current database state"""
    app = create_app()
    with app.app_context():
        result = db.session.execute(db.text('''
            SELECT COUNT(*) FROM visit_records
        '''))
        visit_count = result.scalar()
        
        result = db.session.execute(db.text('''
            SELECT COUNT(*) FROM families
        '''))
        family_count = result.scalar()
        
        result = db.session.execute(db.text('''
            SELECT COUNT(*) FROM users
        '''))
        user_count = result.scalar()
        
        return {
            'visits': visit_count,
            'families': family_count,
            'users': user_count,
        }

def get_token():
    """Login and get access token"""
    print("\n1️⃣ GETTING TOKEN...")
    resp = requests.post(f'{BASE_URL}/auth/login', json={
        'mobile': '9876543210',
        'password': 'test@123'
    })
    
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.status_code}")
        print(resp.text)
        return None
    
    data = resp.json()
    token = data.get('data', {}).get('access_token')
    print(f"✅ Got token: {token[:20]}...")
    return token

def create_test_visit(token):
    """Create a test visit via API"""
    print("\n2️⃣ CREATING VISIT VIA API...")
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'beneficiary_name': f'Test Visit {datetime.now().strftime("%H:%M:%S")}',
        'asha_id': 'ASH001',
        'visit_date': datetime.now().strftime('%Y-%m-%d'),
        'visit_type': 'general',
        'status': 'completed',
        'notes': f'Test at {datetime.now().isoformat()}'
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    resp = requests.post(f'{BASE_URL}/visits/', headers=headers, json=payload)
    
    print(f"Response Status: {resp.status_code}")
    print(f"Response: {resp.text[:300]}")
    
    if resp.status_code in [200, 201]:
        print("✅ Visit created via API")
        return True
    else:
        print(f"❌ Failed to create visit")
        return False

def main():
    print("=" * 70)
    print("📊 RECORD CREATION & PERSISTENCE MONITOR")
    print("=" * 70)
    
    # Check initial state
    print("\n📋 INITIAL DATABASE STATE")
    initial = check_db_records()
    for key, val in initial.items():
        print(f"  {key.capitalize()}: {val}")
    
    # Get token and create visit
    token = get_token()
    if not token:
        return
    
    success = create_test_visit(token)
    
    # Check final state
    print("\n📋 FINAL DATABASE STATE")
    final = check_db_records()
    for key, val in final.items():
        print(f"  {key.capitalize()}: {val}")
    
    # Compare
    print("\n📊 CHANGES")
    for key in initial:
        diff = final[key] - initial[key]
        if diff > 0:
            print(f"  ✅ {key.capitalize()}: +{diff}")
        elif diff < 0:
            print(f"  ⚠️ {key.capitalize()}: {diff}")
        else:
            print(f"  → {key.capitalize()}: unchanged")
    
    print("\n" + "=" * 70)
    if success and final['visits'] > initial['visits']:
        print("✅ RECORDS ARE BEING STORED CORRECTLY")
    elif success and final['visits'] == initial['visits']:
        print("⚠️ API ACCEPTED REQUEST BUT RECORD NOT SAVED TO DATABASE")
        print("   This suggests a database commit issue")
    else:
        print("❌ API REJECTED REQUEST")
        print("   Check payload validation")
    print("=" * 70)

if __name__ == '__main__':
    main()
