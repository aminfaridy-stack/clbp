import joblib
import os
import pandas as pd
import shap
from typing import Dict, Any

# Mock paths for model files
MODEL_PATH = "model/clbp_xgboost_model.pkl"
SHAP_EXPL_PATH = "model/clbp_shap_explainer.pkl"

class MLService:
    def __init__(self):
        try:
            self.model = joblib.load(MODEL_PATH)
            self.explainer = joblib.load(SHAP_EXPL_PATH)
            self.feature_names = ['fabq_score', 'phq9_score', 'pcs_score', 'tsk11_score', 'psqi_score', 'hplp_score', 'rmdq_score', 'nrs_score', 'lefs_score', 'nmq_regions']
            print("ML Model loaded successfully.")
        except FileNotFoundError:
            print(f"Model files not found. Run `python {os.path.abspath('train_model.py')}` to generate them.")
            self.model = None
            self.explainer = None
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
            self.explainer = None

    def predict_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.model or not self.explainer:
            return {
                "risk_percentage": 50,
                "risk_category_fa": "نامشخص",
                "risk_category_en": "Unknown",
                "explanations": {"status": "مدل در دسترس نیست" if self.model else "Model not available"}
            }

        # Convert input data to a DataFrame, handle missing features
        input_df = pd.DataFrame([patient_data], columns=self.feature_names)
        
        # Make a prediction
        prediction_proba = self.model.predict_proba(input_df)[0][1] * 100
        risk_percentage = int(round(prediction_proba))
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(input_df)
        
        # Map feature names to SHAP values
        shap_explanation = {
            feature: round(value, 2)
            for feature, value in zip(self.feature_names, shap_values[0])
        }

        # Determine risk category
        if risk_percentage < 30:
            category_fa = "کم"
            category_en = "Low"
        elif risk_percentage < 70:
            category_fa = "متوسط"
            category_en = "Moderate"
        else:
            category_fa = "زیاد"
            category_en = "High"

        return {
            "risk_percentage": risk_percentage,
            "risk_category_fa": category_fa,
            "risk_category_en": category_en,
            "explanations": shap_explanation
        }

ml_service = MLService()