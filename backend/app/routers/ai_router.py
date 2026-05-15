from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.ai_schemas import LeadScoreInput, ChurnPredictInput, LeadScoreResponse, ChurnPredictionResponse
from app.services.ai_service import ai_service
from app import auth, models, tenant_access
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/ai", tags=["AI"])

@router.post("/score-lead", response_model=LeadScoreResponse)
async def score_lead(
    input_data: LeadScoreInput,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Calculates lead conversion probability and explains key factors.
    """
    try:
        return await ai_service.score_lead(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead scoring failed: {str(e)}")

@router.post("/predict-churn", response_model=ChurnPredictionResponse)
async def predict_churn(
    input_data: ChurnPredictInput,
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Predicts customer churn risk and identifies contributing factors.
    """
    try:
        return await ai_service.predict_churn(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Churn prediction failed: {str(e)}")

@router.get("/analyze-contact/{contact_id}")
async def analyze_contact_full(
    contact_id: str,
    deal_id: str | None = Query(None, description="ID сделки: если доступ к контакту по компании невозможен, проверяется право на эту сделку (как в чате)."),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    Автоматически собирает данные из БД и запускает ИИ-анализ по контакту.
    При открытии с карточки сделки передайте query `deal_id`, чтобы согласовать доступ с правом на сделку.
    """
    if deal_id:
        tenant_access.ensure_chat_contact_access(db, current_user, contact_id, deal_id)
    else:
        tenant_access.ensure_contact_access(db, current_user, contact_id)
    from app import crud
    from app.schemas.ai_schemas import LeadScoreInput, ChurnPredictInput
    
    # 1. Collect features from DB
    features = crud.get_contact_ai_features(db, contact_id)
    
    # 2. Perform AI Analysis
    try:
        lead_analysis = await ai_service.score_lead(LeadScoreInput(**features))
        churn_analysis = await ai_service.predict_churn(ChurnPredictInput(**features))
        
        return {
            "contact_id": contact_id,
            "features": features,
            "analysis": {
                "lead_conversion": lead_analysis,
                "churn_risk": churn_analysis
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Analysis failed: {str(e)}")
