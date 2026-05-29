"""Government schemes route."""
from fastapi import APIRouter, Depends
from app.utils.auth_utils import get_current_user

router = APIRouter()

SCHEMES = [
    {"id": 1, "name": "Janani Suraksha Yojana (JSY)", "category": "Maternal Health", "benefit": "₹1400 for rural delivery", "eligibility": "BPL pregnant women"},
    {"id": 2, "name": "PMMVY", "category": "Maternal Health", "benefit": "₹5000 cash incentive", "eligibility": "First live birth"},
    {"id": 3, "name": "POSHAN Abhiyaan", "category": "Child Nutrition", "benefit": "Supplementary nutrition", "eligibility": "Children 0-6 years"},
    {"id": 4, "name": "Rashtriya Bal Swasthya Karyakram", "category": "Child Health", "benefit": "Free screening & treatment", "eligibility": "Children 0-18 years"},
    {"id": 5, "name": "Mission Indradhanush", "category": "Immunization", "benefit": "Full immunization coverage", "eligibility": "All children under 2"},
    {"id": 6, "name": "Ayushman Bharat", "category": "Health Insurance", "benefit": "₹5 lakh health cover", "eligibility": "Poor & vulnerable families"},
]

@router.get("/schemes")
def get_schemes(current_user=Depends(get_current_user)):
    return {"success": True, "schemes": SCHEMES}
