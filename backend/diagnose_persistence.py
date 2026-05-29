#!/usr/bin/env python
"""
🔍 COMPLETE DATA PERSISTENCE DIAGNOSTIC
========================================
This script checks both frontend and backend for data storage issues.
"""

from app import create_app
from app.extensions import db
from app.models.user import UserModel
from sqlalchemy import text
import json

app = create_app()
ctx = app.app_context()
ctx.push()

print("\n" + "="*70)
print("🔍 ASHA SEVA DATA PERSISTENCE DIAGNOSTIC")
print("="*70)

# 1. DATABASE CONNECTION
print("\n1️⃣ DATABASE CONNECTION")
print("-" * 70)
db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
if 'postgresql' in db_url:
    print("✅ Using PostgreSQL")
    print(f"   Host: {db_url.split('@')[1].split(':')[0] if '@' in db_url else 'unknown'}")
    print(f"   Database: {db_url.split('/')[-1]}")
elif 'sqlite' in db_url:
    print("⚠️ Using SQLite (fallback)")
    print(f"   Path: {db_url}")
else:
    print("❌ Unknown database type")

# 2. TABLE SCHEMA
print("\n2️⃣ DATABASE TABLES & RECORD COUNTS")
print("-" * 70)
tables = {
    'users': 'User Accounts',
    'families': 'Beneficiary Families',
    'family_members': 'Family Members',
    'anc_records': 'Antenatal Care Records',
    'family_planning_records': 'Family Planning Records',
    'visit_records': 'Health Visit Records',
    'children': 'Child Health Records',
    'vaccine_entries': 'Vaccination Entries',
    'scheme_enrollments': 'Scheme Enrollments'
}

with db.engine.connect() as conn:
    for table_name, description in tables.items():
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table_name}'))
            count = result.scalar()
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {table_name:25} ({description:30}): {count:4} records")
        except Exception as e:
            print(f"❌ {table_name:25}: {str(e)[:50]}")

# 3. USERS IN DATABASE
print("\n3️⃣ USER ACCOUNTS")
print("-" * 70)
users = UserModel.query.all()
print(f"Total users: {len(users)}")
for user in users:
    print(f"   • {user.name:30} | Mobile: {user.mobile} | Role: {user.role:12} | Active: {user.is_active}")

# 4. PERSISTENCE CHECK
print("\n4️⃣ DATA PERSISTENCE ISSUES")
print("-" * 70)
issues = []

# Check if tables are empty except users
with db.engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM families'))
    if result.scalar() == 0:
        issues.append("❌ No families registered - beneficiary data not being saved")
    
    result = conn.execute(text('SELECT COUNT(*) FROM visit_records'))
    if result.scalar() == 0:
        issues.append("⚠️ No visit records - health visit data not being synced")

# Check if auth tokens are configured
if app.config.get('JWT_SECRET_KEY') == 'jwt-secret-change-me':
    issues.append("⚠️ JWT_SECRET_KEY not changed from default")

if not issues:
    print("✅ No obvious issues found")
else:
    for issue in issues:
        print(issue)

# 5. FRONTEND-BACKEND SYNC STATUS
print("\n5️⃣ FRONTEND-BACKEND INTEGRATION")
print("-" * 70)
print("Frontend stores data in:")
print("  📱 SharedPreferences (local): User profile, auth tokens")
print("  🔒 SecureStorage (encrypted): Access/refresh tokens")
print("")
print("Backend should store:")
print("  🗄️ PostgreSQL: All beneficiary, health, and visit data")
print("")
print("To verify data sync:")
print("  1. Login via Flutter app")
print("  2. Create a beneficiary (family) record")
print("  3. Run this script again to see if record appears in DB")
print("  4. Check API logs: tail -f backend/logs/asha.log")

print("\n" + "="*70)
print("💡 NEXT STEPS:")
print("="*70)
print("""
If families/health data is NOT appearing:
  
  1. Check Flutter app console for API errors
     - Look for 401 (auth), 400 (validation), 500 (server) errors
  
  2. Verify backend is receiving requests:
     - Run: tail -f backend/logs/asha.log
     - Try creating data in app
     - Watch for POST /api/families or other endpoints
  
  3. Verify auth tokens are valid:
     - Check if refresh token endpoint is working
     - POST /api/auth/refresh
  
  4. Check if data is being committed:
     - Database transaction logs show: "💾 Database transaction committed"
     - Look for rollback messages: "↩️ Database transaction rolled back"
""")

print("="*70 + "\n")
