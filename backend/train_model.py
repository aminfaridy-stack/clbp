import joblib
import pandas as pd
import numpy as np
import xgboost as xgb
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# A script to generate a synthetic dataset and train a mock ML model
# so the backend can run without a pre-existing model file.
def generate_synthetic_data(num_samples=500):
    data = {}
    data['fabq_score'] = np.random.randint(0, 97, num_samples)
    data['phq9_score'] = np.random.randint(0, 28, num_samples)
    data['pcs_score'] = np.random.randint(0, 53, num_samples)
    data['tsk11_score'] = np.random.randint(11, 45, num_samples)
    data['psqi_score'] = np.random.randint(0, 22, num_samples)
    data['hplp_score'] = np.random.randint(52, 209, num_samples)
    data['rmdq_score'] = np.random.randint(0, 25, num_samples)
    data['nrs_score'] = np.random.randint(0, 11, num_samples)
    data['lefs_score'] = np.random.randint(0, 81, num_samples)
    data['nmq_regions'] = np.random.randint(0, 10, num_samples)
    
    df = pd.DataFrame(data)
    
    # Create a synthetic chronicity target
    df['chronicity'] = ((df['phq9_score'] > 10) | (df['pcs_score'] > 30) | (df['rmdq_score'] > 12) | (df['nrs_score'] > 6)).astype(int)
    
    return df, ['fabq_score', 'phq9_score', 'pcs_score', 'tsk11_score', 'psqi_score', 'hplp_score', 'rmdq_score', 'nrs_score', 'lefs_score', 'nmq_regions']

def train_and_save_model():
    print("Generating synthetic data...")
    df, feature_names = generate_synthetic_data()
    X = df[feature_names]
    y = df['chronicity']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model trained with accuracy: {accuracy:.2f}")

    print("Generating SHAP explainer...")
    explainer = shap.TreeExplainer(model)
    
    # Create model directory if it doesn't exist
    import os
    if not os.path.exists('model'):
        os.makedirs('model')

    # Save the model and explainer
    model_path = 'model/clbp_xgboost_model.pkl'
    explainer_path = 'model/clbp_shap_explainer.pkl'
    joblib.dump(model, model_path)
    joblib.dump(explainer, explainer_path)
    
    print(f"Model saved to {model_path}")
    print(f"SHAP explainer saved to {explainer_path}")

if __name__ == '__main__':
    train_and_save_model()