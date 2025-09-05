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
    
    # Check if a user with a specific email exists to prevent re-seeding
    if db_session.query(User).filter(User.email == "admin@clbp.com").first():
        print("Database already seeded. Skipping...")
        db_session.close()
        return

    print("Seeding demo users...")
    from auth import get_password_hash
    admin_user = User(name="مدیر", email="admin@clbp.com", password_hash=get_password_hash("admin123"), role="admin")
    clinician_user = User(name="پزشک", email="clinician@clbp.com", password_hash=get_password_hash("clinician123"), role="clinician")
    patient_user = User(name="بیمار", email="patient@clbp.com", password_hash=get_password_hash("patient123"), role="patient")
    db_session.add_all([admin_user, clinician_user, patient_user])
    db_session.commit()
    print("Demo users created.")

    print("Seeding questionnaires...")
    # Example for PHQ-9. Extend for all 10 questionnaires.
    phq9 = Questionnaire(
        key="phq9",
        title_fa="پرسشنامه سلامت بیمار (PHQ-9)",
        title_en="Patient Health Questionnaire (PHQ-9)",
        description_fa="لطفاً در مورد دفعات مشکلات زیر در ۲ هفته گذشته به دقت پاسخ دهید.",
        description_en="Over the last 2 weeks, how often have you been bothered by the following problems?"
    )
    
    phq9_questions = [
        Question(
            questionnaire=phq9, index=1,
            text_fa="احساس بی‌علاقگی یا عدم لذت بردن از انجام کارها",
            text_en="Little interest or pleasure in doing things",
            input_type="likert_4",
            options_fa=["اصلا", "چند روزی", "بیش از نیمی از روزها", "تقریبا هر روز"],
            options_en=["Not at all", "Several days", "More than half the days", "Nearly every day"],
        )
        # Add other PHQ-9 questions here...
    ]
    db_session.add(phq9)
    db_session.add_all(phq9_questions)
    
    db_session.commit()
    print("Questionnaires seeded.")
    db_session.close()

if __name__ == "__main__":
    seed_database()