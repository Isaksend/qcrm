import joblib
import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, List, Tuple
from app.schemas.ai_schemas import LeadScoreInput, ChurnPredictInput, LeadScoreResponse, ChurnPredictionResponse, SHAPFactor

class AIPredictionService:
    def __init__(self):
        self.lead_model = None
        self.lead_explainer = None
        self.churn_model = None
        self.churn_explainer = None
        self.features = ['activity_count_30d', 'days_since_last_contact', 'total_deal_value', 'interaction_score']

    def load_artifacts(self, models_path: str = "models/"):
        """Loads models and explainers into memory."""
        try:
            self.lead_model = joblib.load(f"{models_path}lead_scoring_pipeline.joblib")
            self.lead_explainer = joblib.load(f"{models_path}lead_scoring_explainer.joblib")
            self.churn_model = joblib.load(f"{models_path}churn_prediction_pipeline.joblib")
            self.churn_explainer = joblib.load(f"{models_path}churn_prediction_explainer.joblib")
            print("AI Models and Explainers loaded successfully.")
        except Exception as e:
            print(f"Error loading AI artifacts: {e}")
            # In production, we might want to raise an error or use fallback models

    def _get_risk_category(self, prob: float) -> str:
        if prob < 0.3: return "Low"
        if prob < 0.7: return "Medium"
        return "High"

    def _extract_shap_factors(self, explainer, transformed_data, feature_names: List[str]) -> List[SHAPFactor]:
        """Extracts top 3 positive and negative factors from SHAP values."""
        # Get raw shap values
        shap_result = explainer.shap_values(transformed_data)
        
        # Robust handling of different SHAP output formats:
        # 1. If it's a list (common for RandomForest: [class0_values, class1_values])
        if isinstance(shap_result, list):
            # Take values for the positive class (usually index 1)
            # and take the first (and only) row since we predict for 1 sample
            val = shap_result[1][0] if len(shap_result) > 1 else shap_result[0][0]
        # 2. If it's a 3D array (some models/versions)
        elif len(shap_result.shape) == 3:
            val = shap_result[0, :, 1]
        # 3. If it's a 2D array (common for GradientBoosting: [sample_index, feature_index])
        elif len(shap_result.shape) == 2:
            val = shap_result[0]
        # 4. Fallback
        else:
            val = shap_result

        factors = []
        for i, impact in enumerate(val):
            # Ensure impact is a float, not an array
            actual_impact = float(impact) if hasattr(impact, "__len__") == False else float(impact[0])
            factors.append(SHAPFactor(
                feature=feature_names[i],
                impact=actual_impact,
                description=f"{'Positive' if actual_impact > 0 else 'Negative'} impact on outcome"
            ))
        
        # Sort by absolute impact and take top factors
        sorted_factors = sorted(factors, key=lambda x: abs(x.impact), reverse=True)
        return sorted_factors[:3]

    async def score_lead(self, data: LeadScoreInput) -> LeadScoreResponse:
        if not self.lead_model:
            raise RuntimeError("Lead scoring model not loaded")

        input_df = pd.DataFrame([data.model_dump()])
        
        # Feature Engineering (placeholder for complex logic)
        # Here we use the raw data as features match our mock training
        X = input_df[self.features].values
        
        # Predict
        prob = float(self.lead_model.predict_proba(X)[0][1])
        
        # Explain
        X_transformed = self.lead_model.named_steps['preprocessing'].transform(X)
        top_factors = self._extract_shap_factors(self.lead_explainer, X_transformed, self.features)
        
        return LeadScoreResponse(
            probability=round(prob * 100, 2),
            risk_category=self._get_risk_category(prob),
            top_factors=top_factors
        )

    async def predict_churn(self, data: ChurnPredictInput) -> ChurnPredictionResponse:
        if not self.churn_model:
            raise RuntimeError("Churn prediction model not loaded")

        input_df = pd.DataFrame([data.model_dump()])
        X = input_df[self.features].values
        
        # Predict
        prob = float(self.churn_model.predict_proba(X)[0][1])
        
        # Explain
        X_transformed = self.churn_model.named_steps['preprocessing'].transform(X)
        top_factors = self._extract_shap_factors(self.churn_explainer, X_transformed, self.features)
        
        return ChurnPredictionResponse(
            probability=round(prob * 100, 2),
            risk_category=self._get_risk_category(prob),
            top_factors=top_factors
        )

# Global instance for service
ai_service = AIPredictionService()
