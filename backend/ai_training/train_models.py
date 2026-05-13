import os
import joblib
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import shap
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, roc_auc_score, precision_recall_curve, auc
from imblearn.over_sampling import SMOTE
from typing import Tuple, Dict, Any

# Ensure directories exist
os.makedirs("models", exist_ok=True)

def generate_mock_data(n_samples: int = 1000) -> pd.DataFrame:
    """Generates synthetic data for demonstration."""
    np.random.seed(42)
    data = pd.DataFrame({
        'activity_count_30d': np.random.poisson(10, n_samples),
        'days_since_last_contact': np.random.exponential(15, n_samples),
        'total_deal_value': np.random.gamma(500, 10, n_samples),
        'interaction_score': np.random.uniform(0, 1, n_samples),
        'is_lead_converted': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'is_churned': np.random.choice([0, 1], n_samples, p=[0.9, 0.1])
    })
    return data

def build_preprocessing_pipeline() -> Pipeline:
    """Builds the standard preprocessing pipeline."""
    return Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

def train_model(
    name: str, 
    model_obj: Any, 
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    X_test: np.ndarray, 
    y_test: np.ndarray,
    params: Dict[str, Any]
) -> Tuple[Pipeline, shap.Explainer]:
    """Trains a model with MLflow tracking and SHAP calculation."""
    
    with mlflow.start_run(run_name=name):
        # Preprocessing & Balancing
        smote = SMOTE(random_state=42)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        
        # Build full pipeline
        pipeline = Pipeline([
            ('preprocessing', build_preprocessing_pipeline()),
            ('model', model_obj)
        ])
        
        # Train
        pipeline.fit(X_res, y_res)
        
        # Metrics
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_prob)
        precision, recall, _ = precision_recall_curve(y_test, y_prob)
        pr_auc = auc(recall, precision)
        
        # Logging
        mlflow.log_params(params)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("roc_auc", roc_auc)
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.sklearn.log_model(pipeline, "model")
        
        # SHAP
        # Note: Explainer needs the transformed data
        X_test_transformed = pipeline.named_steps['preprocessing'].transform(X_test)
        explainer = shap.TreeExplainer(pipeline.named_steps['model'])
        
        print(f"Model {name} trained. F1: {f1:.4f}, ROC AUC: {roc_auc:.4f}")
        
        return pipeline, explainer

if __name__ == "__main__":
    df = generate_mock_data()
    features = ['activity_count_30d', 'days_since_last_contact', 'total_deal_value', 'interaction_score']
    
    # 1. Lead Scoring Model
    X_lead = df[features].values
    y_lead = df['is_lead_converted'].values
    X_train, X_test, y_train, y_test = train_test_split(X_lead, y_lead, test_size=0.2, random_state=42)
    
    gb_params = {"n_estimators": 100, "learning_rate": 0.1, "max_depth": 3}
    lead_model, lead_explainer = train_model(
        "Lead_Scoring", 
        GradientBoostingClassifier(**gb_params),
        X_train, y_train, X_test, y_test, gb_params
    )
    
    # 2. Churn Prediction Model
    X_churn = df[features].values
    y_churn = df['is_churned'].values
    X_train, X_test, y_train, y_test = train_test_split(X_churn, y_churn, test_size=0.2, random_state=42)
    
    rf_params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
    churn_model, churn_explainer = train_model(
        "Churn_Prediction",
        RandomForestClassifier(**rf_params),
        X_train, y_train, X_test, y_test, rf_params
    )
    
    # Export Artifacts
    joblib.dump(lead_model, "models/lead_scoring_pipeline.joblib")
    joblib.dump(lead_explainer, "models/lead_scoring_explainer.joblib")
    joblib.dump(churn_model, "models/churn_prediction_pipeline.joblib")
    joblib.dump(churn_explainer, "models/churn_prediction_explainer.joblib")
    
    print("All models and explainers exported to models/ directory.")
