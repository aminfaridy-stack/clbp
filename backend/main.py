import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import json
import random
from typing import List, Dict, Any, Optional

import db, auth, ml_service
from db import User, UserCreate, Token, ResponseIn, Score, Prediction, PredictionResult, get_db

app = FastAPI(
    title="CLBP Prediction API",
    description="Backend API for the Chronic Low Back Pain Predictive System.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
origins = [
    "http://localhost",
    "http://localhost:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Endpoints ---
@app.post("/auth/register", response_model=db.UserInDB)
def register_user(user: db.UserCreate, db_session: Session = Depends(get_db)):
    db_user = db_session.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    # Default role to 'patient'
    new_user = User(name=user.name, email=user.email, password_hash=hashed_password, role='patient')
    db_session.add(new_user)
    db_session.commit()
    db_session.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=Token)
def login_for_access_token(form_data: dict, db_session: Session = Depends(get_db)):
    email = form_data.get('username')
    password = form_data.get('password')
    user = db_session.query(User).filter(User.email == email).first()
    if not user or not auth.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_info": user}

# --- Questionnaire and Response Endpoints ---
@app.get("/api/questionnaires", response_model=List[db.QuestionnaireSchema])
def get_questionnaires(db_session: Session = Depends(get_db)):
    return db_session.query(db.Questionnaire).all()

@app.get("/api/questionnaires/{key}", response_model=db.QuestionnaireSchema)
def get_questionnaire_by_key(key: str, db_session: Session = Depends(get_db)):
    q = db_session.query(db.Questionnaire).filter(db.Questionnaire.key == key).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return q

@app.post("/api/responses")
def save_responses(responses: ResponseIn, db_session: Session = Depends(get_db)):
    for resp in responses.responses:
        db_response = db.Response(
            user_id=responses.user_id,
            questionnaire_id=responses.questionnaire_id,
            time_point=responses.time_point,
            question_id=resp['question_id'],
            answer=resp['answer']
        )
        db_session.add(db_response)
    db_session.commit()
    return {"message": "Responses saved successfully"}

@app.post("/api/scores/validate")
def validate_and_store_scores(payload: dict, db_session: Session = Depends(get_db)):
    user_id = payload.get('user_id')
    questionnaire_id = payload.get('questionnaire_id')
    time_point = payload.get('time_point')
    score_data = payload.get('score_data')
    
    db_score = Score(
        user_id=user_id,
        questionnaire_id=questionnaire_id,
        time_point=time_point,
        score=score_data.get('score'),
        category_fa=score_data.get('category_fa'),
        category_en=score_data.get('category_en'),
        breakdown_json=score_data.get('breakdown')
    )
    db_session.add(db_score)
    db_session.commit()
    return {"message": "Score validated and stored"}

@app.post("/api/predict", response_model=PredictionResult)
def get_prediction(payload: Dict[str, Any], db_session: Session = Depends(get_db)):
    user_id = payload.get('user_id')
    time_point = payload.get('time_point')
    patient_data = payload.get('patient_data') # Should be a dictionary of scores

    prediction = ml_service.ml_service.predict_risk(patient_data)
    
    # Store the prediction result in the database
    db_prediction = Prediction(
        user_id=user_id,
        time_point=time_point,
        model_version="v1.0.0", # Placeholder for real versioning
        risk_percentage=prediction['risk_percentage'],
        risk_category_fa=prediction['risk_category_fa'],
        risk_category_en=prediction['risk_category_en'],
        shap_summary_json=prediction['explanations']
    )
    db_session.add(db_prediction)
    db_session.commit()

    return prediction

# --- Admin Endpoints (RBAC protected) ---
@app.get("/admin/patients", dependencies=[Depends(auth.is_clinician_or_admin)])
def get_patients(db_session: Session = Depends(get_db)):
    return db_session.query(db.User).filter(db.User.role == 'patient').all()

@app.get("/admin/patients/{user_id}/timeline", dependencies=[Depends(auth.is_clinician_or_admin)])
def get_patient_timeline(user_id: int, db_session: Session = Depends(get_db)):
    scores = db_session.query(db.Score).filter(db.Score.user_id == user_id).order_by(db.Score.created_at).all()
    predictions = db_session.query(db.Prediction).filter(db.Prediction.user_id == user_id).order_by(db.Prediction.created_at).all()
    return {"scores": scores, "predictions": predictions}

@app.get("/admin/analytics/overview", dependencies=[Depends(auth.is_clinician_or_admin)])
def get_analytics_overview(db_session: Session = Depends(get_db)):
    total_patients = db_session.query(db.User).filter(db.User.role == 'patient').count()
    total_scores = db_session.query(db.Score).count()
    high_risk_predictions = db_session.query(db.Prediction).filter(db.Prediction.risk_percentage > 70).count()
    
    # Placeholder analytics, replace with real queries
    avg_scores = {
        'phq9': random.randint(5, 15),
        'nrs': random.randint(3, 8),
    }

    return {
        "total_patients": total_patients,
        "total_questionnaires_completed": total_scores,
        "patients_with_high_risk": high_risk_predictions,
        "average_scores": avg_scores,
    }

@app.post("/admin/models", dependencies=[Depends(auth.is_admin)])
def upload_new_model():
    # Placeholder for model upload logic
    return {"message": "Model upload not yet implemented."}

@app.get("/admin/audit-logs", dependencies=[Depends(auth.is_admin)])
def get_audit_logs(db_session: Session = Depends(get_db)):
    logs = db_session.query(db.AuditLog).order_by(db.AuditLog.created_at.desc()).limit(100).all()
    return logs