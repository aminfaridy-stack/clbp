# AI-Powered Predictive System for Chronic Low Back Pain (CLBP)

This is a full-stack, containerized web application designed to predict the risk of chronicity (>12 weeks) in patients with non-specific low back pain. The application features a patient-facing portal for completing standardized questionnaires and a secure admin/clinician dashboard for data analytics and model management.

## 🚀 Features

* **Primary Language**: Full Farsi (fa-IR) support with a toggle for English.
* **Typography**: Uses the Farsi-friendly Vazirmatn font.
* **User Roles**: Patient, Clinician, and Admin with Role-Based Access Control (RBAC).
* **Data Collection**: Multi-step forms for 10 standardized questionnaires (FABQ, PHQ-9, PCS, TSK-11, PSQI, HPLP II, RMDQ, NRS, NMQ, LEFS) at T0, T1, and T2 time points.
* **Predictive Analytics**: An ML model (XGBoost) predicts chronicity risk based on patient data from all time points. Includes SHAP for model explainability.
* **Analytics Dashboard**: A comprehensive dashboard for admins/clinicians with deep data insights, including score distributions, correlations, and model performance metrics.
* **Containerized Deployment**: The entire application is containerized with Docker and orchestrated using `docker-compose`, making it easy to deploy on any server.

## 📦 Tech Stack

* **Frontend**: Streamlit, with custom CSS for styling and `streamlit-i18n` for localization.
* **Backend**: FastAPI, for a fast and efficient API.
* **Database**: PostgreSQL, for secure and scalable data storage.
* **Machine Learning**: `scikit-learn` and `XGBoost` for predictive modeling; `SHAP` for explainability.
* **Auth**: JWT with Refresh Tokens for secure authentication.
* **DevOps**: Docker, `docker-compose`, Nginx for production-grade deployment.

## 🛠️ Setup and Run

1.  **Clone this repository**: (Note: This is a simulated `README.md` for a single-file script output.)
2.  **Create project files**: Follow the instructions in the main script to create the files from the provided code blocks.
3.  **Configure environment variables**:
    * Copy `.env.example` to `.env`.
    * Edit the `.env` file to configure database credentials and JWT secrets.
4.  **Build and run the containers**:
    * From the root directory, execute:
        ```bash
        docker-compose up --build
        ```
    * This command will build the Docker images for the frontend and backend, start the PostgreSQL database, and run Nginx.

5.  **Access the application**:
    * **Patient/Clinician Portal**: Navigate to `http://localhost:8501`.
    * **Admin Panel**: Navigate to `http://localhost:8501/?page=admin_login`.

## 📂 File Structure

The project is structured into three main services: `backend`, `frontend`, and `nginx`, all managed by `docker-compose`.