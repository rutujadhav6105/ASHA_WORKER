#!/usr/bin/env python
"""Check what data is stored in the database."""

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
ctx = app.app_context()
ctx.push()

# Query table counts
tables_to_check = [
    'families', 
    'anc_records', 
    'family_planning_records', 
    'visit_records', 
    'children', 
    'vaccine_entries',
    'scheme_enrollments'
]

print("\n📊 DATABASE DATA SUMMARY\n" + "="*50)

with db.engine.connect() as conn:
    for table in tables_to_check:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            status = "✅" if count > 0 else "⚠️"
            print(f"{status} {table:30} : {count:6} records")
        except Exception as e:
            print(f"❌ {table:30} : Error - {str(e)[:40]}")

print("="*50)
