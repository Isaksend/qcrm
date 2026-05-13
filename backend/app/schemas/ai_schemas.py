from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class AIInputBase(BaseModel):
    activity_count_30d: Optional[int] = Field(None, description="Number of activities in last 30 days")
    days_since_last_contact: Optional[int] = Field(None, description="Days since last customer interaction")
    total_deal_value: float = Field(0.0, ge=0)
    interaction_score: float = Field(0.5, ge=0, le=1)

class LeadScoreInput(AIInputBase):
    pass

class ChurnPredictInput(AIInputBase):
    pass

class SHAPFactor(BaseModel):
    feature: str
    impact: float
    description: str

class AIPredictionResponse(BaseModel):
    probability: float = Field(..., description="Probability in %")
    risk_category: str = Field(..., description="Low, Medium, or High")
    top_factors: List[SHAPFactor]
    
class LeadScoreResponse(AIPredictionResponse):
    pass

class ChurnPredictionResponse(AIPredictionResponse):
    pass
