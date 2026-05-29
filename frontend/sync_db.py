import sys
import os

# Add backend to path
sys.path.append('c:/FlutterProject/backend')

try:
    from app.database import Base, engine
    from app.models.models import User, Patient, Pregnancy, ANCVisit, Immunization, HomeVisit, MedicineStock, Alert, Report, TrainingRecord, Village, SupervisorNote
    
    print("Recreating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully.")
except Exception as e:
    print(f"Error: {e}")
