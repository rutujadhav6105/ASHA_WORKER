#!/usr/bin/env python3
"""
Diagnose visit record creation flow.
Logs each step to identify where records fail to persist.
"""
import json
import logging
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = 'http://localhost:5000/api'

def create_visit_with_diagnostics():
    """Create a visit and log each step"""
    print("\n" + "=" * 80)
    print("VISIT CREATION DIAGNOSTICS")
    print("=" * 80)
    
    # Step 1: Login
    logger.info("Step 1: Authenticating...")
    login_resp = requests.post(f'{BASE_URL}/auth/login', json={
        'mobile': '9876543210',
        'password': 'test@123'
    })
    
    if login_resp.status_code != 200:
        logger.error(f"Login failed: {login_resp.status_code}")
        print(login_resp.text)
        return False
    
    token = login_resp.json()['data']['access_token']
    logger.info(f"✅ Authenticated. Token: {token[:20]}...")
    
    # Step 2: Get database count before
    logger.info("\nStep 2: Checking database before creation...")
    from app import create_app
    from app.extensions import db
    
    app = create_app()
    with app.app_context():
        result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
        count_before = result.scalar()
        logger.info(f"Records before: {count_before}")
    
    # Step 3: Create visit via API
    logger.info("\nStep 3: Creating visit via API...")
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'beneficiary_name': f'Diagnostic Test {datetime.now().strftime("%H:%M:%S")}',
        'asha_id': 'ASH001',
        'visit_date': datetime.now().strftime('%Y-%m-%d'),
        'visit_type': 'general',
        'status': 'completed',
        'notes': 'Diagnostic test'
    }
    
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    create_resp = requests.post(f'{BASE_URL}/visits/', headers=headers, json=payload)
    logger.info(f"API Response Status: {create_resp.status_code}")
    
    if create_resp.status_code in [200, 201]:
        response_data = create_resp.json()
        logger.info(f"✅ API accepted request")
        logger.info(f"Response: {json.dumps(response_data, indent=2)[:500]}")
    else:
        logger.error(f"❌ API rejected request")
        logger.error(f"Response: {create_resp.text[:500]}")
        return False
    
    # Step 4: Check database after
    logger.info("\nStep 4: Checking database after creation...")
    with app.app_context():
        result = db.session.execute(db.text('SELECT COUNT(*) FROM visit_records'))
        count_after = result.scalar()
        logger.info(f"Records after: {count_after}")
        
        if count_after > count_before:
            logger.info(f"✅ SUCCESS! Created {count_after - count_before} record(s)")
            
            # Show the new record
            result = db.session.execute(db.text('''
                SELECT beneficiary_name, visit_type, created_at 
                FROM visit_records 
                ORDER BY created_at DESC 
                LIMIT 1
            '''))
            row = result.first()
            if row:
                logger.info(f"New record: {row[0]} ({row[1]})")
            return True
        else:
            logger.error(f"❌ FAILURE! API accepted but NO record created")
            logger.error("Database count unchanged - data was not committed")
            return False

if __name__ == '__main__':
    success = create_visit_with_diagnostics()
    print("\n" + "=" * 80)
    if success:
        print("✅ RECORD CREATED AND PERSISTED")
    else:
        print("❌ RECORD NOT PERSISTED - CHECK LOG ABOVE")
    print("=" * 80 + "\n")
