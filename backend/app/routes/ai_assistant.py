"""AI Assistant route."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.utils.auth_utils import get_current_user

router = APIRouter()

class AIRequest(BaseModel):
    question: str
    language: Optional[str] = "en"
    context: Optional[str] = None

HEALTH_KNOWLEDGE = {
    "anemia": "Anemia in pregnancy requires daily IFA tablets. Hemoglobin < 7g/dL is severe and needs referral.",
    "vaccination": "Vaccination schedule: BCG at birth, OPV + Hepatitis B at 6/10/14 weeks, MMR at 9 months.",
    "malnutrition": "SAM children need RUTF and referral to NRC. MAM children need supplementary nutrition through ICDS.",
    "hypertension": "BP > 140/90 in pregnancy is hypertension and requires immediate referral to PHC/CHC.",
    "breastfeeding": "Exclusive breastfeeding for 6 months is recommended. Start within 1 hour of birth.",
}

@router.post("/ai-assistant")
def ask_ai(body: AIRequest, current_user=Depends(get_current_user)):
    question_lower = body.question.lower()
    answer = "I can help with maternal health, child nutrition, immunization, and government schemes. Please ask a specific health question."
    
    for keyword, response in HEALTH_KNOWLEDGE.items():
        if keyword in question_lower:
            answer = response
            break

    return {
        "success": True,
        "answer": answer,
        "language": body.language,
        "disclaimer": "This is general health information. Always refer to qualified medical professionals for clinical decisions.",
    }
