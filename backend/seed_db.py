import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, User, Questionnaire, Question

# Database URL
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()

    # --- Seed Users (Idempotent) ---
    if not db_session.query(User).filter(User.email == "admin@clbp.com").first():
        print("Seeding demo users...")
        from auth import get_password_hash
        admin_user = User(name="مدیر", email="admin@clbp.com", password_hash=get_password_hash("admin123"), role="admin")
        clinician_user = User(name="پزشک", email="clinician@clbp.com", password_hash=get_password_hash("clinician123"), role="clinician")
        patient_user = User(name="بیمار", email="patient@clbp.com", password_hash=get_password_hash("patient123"), role="patient")
        db_session.add_all([admin_user, clinician_user, patient_user])
        db_session.commit()
        print("Demo users created.")
    else:
        print("Demo users already exist. Skipping.")

    # --- Seed Questionnaires (Idempotent) ---
    print("Seeding questionnaires...")

    # 1. Demographic Questionnaire
    if not db_session.query(Questionnaire).filter(Questionnaire.key == "demographic").first():
        print("Seeding Demographic questionnaire...")
        demographic_q = Questionnaire(
            key="demographic",
            title_fa="اطلاعات دموگرافیک",
            title_en="Demographic Information",
            description_fa="لطفاً اطلاعات زیر را با دقت تکمیل نمایید.",
            description_en="Please fill out the following information carefully."
        )
        db_session.add(demographic_q)
        db_session.flush() # To get the ID for the questions

        demographic_questions = [
            Question(questionnaire_id=demographic_q.id, index=1, text_fa="سن", text_en="Age", input_type="number_input", options_fa=[], options_en=[]),
            Question(questionnaire_id=demographic_q.id, index=2, text_fa="جنسیت", text_en="Gender", input_type="radio", options_fa=["مرد", "زن"], options_en=["Male", "Female"]),
            Question(questionnaire_id=demographic_q.id, index=3, text_fa="سطح تحصیلات", text_en="Education Level", input_type="selectbox", options_fa=["زیر دیپلم", "دیپلم", "کارشناسی", "کارشناسی ارشد", "دکتری"], options_en=["Below High School", "High School", "Bachelor's", "Master's", "PhD"]),
            Question(questionnaire_id=demographic_q.id, index=4, text_fa="وضعیت تاهل", text_en="Marital Status", input_type="selectbox", options_fa=["مجرد", "متاهل", "سایر"], options_en=["Single", "Married", "Other"]),
            Question(questionnaire_id=demographic_q.id, index=5, text_fa="وضعیت اشتغال", text_en="Employment Status", input_type="selectbox", options_fa=["شاغل", "بیکار", "دانشجو", "بازنشسته"], options_en=["Employed", "Unemployed", "Student", "Retired"]),
        ]
        db_session.add_all(demographic_questions)
        print("Demographic questionnaire seeded.")
    else:
        print("Demographic questionnaire already exists. Skipping.")

    # 2. PHQ-9 Questionnaire
    if not db_session.query(Questionnaire).filter(Questionnaire.key == "phq9").first():
        print("Seeding PHQ-9 questionnaire...")
        phq9 = Questionnaire(
            key="phq9",
            title_fa="پرسشنامه سلامت بیمار (PHQ-9)",
            title_en="Patient Health Questionnaire (PHQ-9)",
            description_fa="لطفاً در مورد دفعات مشکلات زیر در ۲ هفته گذشته به دقت پاسخ دهید.",
            description_en="Over the last 2 weeks, how often have you been bothered by the following problems?"
        )
        db_session.add(phq9)
        db_session.flush()

        phq9_questions = [
            Question(
                questionnaire_id=phq9.id, index=1,
                text_fa="احساس بی‌علاقگی یا عدم لذت بردن از انجام کارها",
                text_en="Little interest or pleasure in doing things",
                input_type="likert_4",
                options_fa=["اصلا", "چند روزی", "بیش از نیمی از روزها", "تقریبا هر روز"],
                options_en=["Not at all", "Several days", "More than half the days", "Nearly every day"],
            )
            # Add other PHQ-9 questions here...
        ]
        db_session.add_all(phq9_questions)
        print("PHQ-9 questionnaire seeded.")
    else:
        print("PHQ-9 questionnaire already exists. Skipping.")
    
    db_session.commit()
    print("Finished seeding questionnaires.")
    db_session.close()

if __name__ == "__main__":
    seed_database()