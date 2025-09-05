import streamlit as st
import requests
import json
from streamlit.components.v1 import html
from datetime import datetime
import time
import pandas as pd

# Get environment variables
API_URL = "http://backend:8000"
BACKEND_URL = "http://localhost:8000"

# --- Streamlit Configuration and Styling ---
st.set_page_config(
    page_title="CLBP Predictive System",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load translations
import yaml
import json
# ... rest of your imports

# For simplicity in this single script, we'll manually load the translations
with open("translations.yml", "r", encoding="utf-8") as f:
    translations = yaml.safe_load(f)

if 'locale' not in st.session_state:
    st.session_state['locale'] = 'fa'

_ = translations[st.session_state['locale']]

# Inject custom CSS for RTL and font
with open("static/style.css") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# --- State Management ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "page" not in st.session_state:
    st.session_state.page = "home"
if "form_data" not in st.session_state:
    st.session_state.form_data = {}
if "form_step" not in st.session_state:
    st.session_state.form_step = 0
if "questionnaires" not in st.session_state:
    st.session_state.questionnaires = {}
if "selected_time_point" not in st.session_state:
    st.session_state.selected_time_point = "t0"
if "persian_numerals" not in st.session_state:
    st.session_state.persian_numerals = True

# --- Helper Functions ---
def get_persian_numerals(number):
    if st.session_state.persian_numerals:
        return str(number).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
    return str(number)

def persian_likert_labels(options):
    if st.session_state.persian_numerals:
        return [f"{get_persian_numerals(i)} - {option}" for i, option in enumerate(options)]
    return [f"{i} - {option}" for i, option in enumerate(options)]

def score_phq9(answers):
    score = sum(answers.values())
    if score >= 20: category_fa, category_en = "شدید", "Severe"
    elif score >= 15: category_fa, category_en = "متوسط تا شدید", "Mod-Severe"
    elif score >= 10: category_fa, category_en = "متوسط", "Moderate"
    elif score >= 5: category_fa, category_en = "خفیف", "Mild"
    else: category_fa, category_en = "حداقلی", "Minimal"
    return score, category_fa, category_en

def score_rmdq(answers):
    score = sum(answers.values())
    category_fa, category_en = "عادی", "Normal"
    if score >= 12: category_fa, category_en = "ناتوانی شدید", "Severe Disability"
    return score, category_fa, category_en

def display_top_bar():
    # This container provides a styled background and border for the top bar
    with st.container():
        st.markdown("""
        <style>
            div[data-testid="stHorizontalBlock"] {
                align-items: center;
            }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([4, 2, 2, 2])

        with col1:
            st.markdown(f"### {_['app_name']}", unsafe_allow_html=True)

        with col2:
            if st.button(f"🛡️ {_['admin_link']}", key="admin_button", use_container_width=True):
                st.session_state.page = "admin_login"
                st.rerun()

        with col3:
            if st.button(f"🌐 {_['lang_toggle']}", key="lang_button", use_container_width=True):
                st.session_state.locale = 'en' if st.session_state.locale == 'fa' else 'fa'
                st.rerun()

        with col4:
            persian_nums_on = st.toggle(
                f"🔢 {_['persian_numerals_toggle']}",
                value=st.session_state.persian_numerals,
                key="num_toggle"
            )
            st.session_state.persian_numerals = persian_nums_on

display_top_bar()

# --- Page Rendering Functions ---
def render_home():
    st.title(_['app_title'])
    st.write(_['home_intro'])
    if not st.session_state.logged_in:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(_['login']):
                st.session_state.page = "login"
                st.rerun()
        with col2:
            if st.button(_['register']):
                st.session_state.page = "register"
                st.rerun()
    else:
        st.subheader(f"👋 {st.session_state.user_info['name']}، خوش آمدید!")
        if st.session_state.user_info['role'] == "patient":
            render_patient_dashboard()
        else:
            st.warning("Only patients have a dashboard.")

def render_login():
    with st.container(border=True):
        st.title(_['login'])

        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown("📧")
        with col2:
            email = st.text_input(_['email'], key="login_email", label_visibility="collapsed")

        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown("🔒")
        with col2:
            password = st.text_input(_['password'], type="password", key="login_pass", label_visibility="collapsed")

        if st.button(_['login']):
            with st.spinner(_['processing']):
                try:
                    response = requests.post(f"{API_URL}/auth/login", json={"username": email, "password": password})
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.token = token_data['access_token']
                        st.session_state.user_info = token_data['user_info']
                        st.session_state.page = "home"
                        st.success(_['login_success'])
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(_['login_error'])
                except requests.exceptions.RequestException as e:
                    st.error(f"{_['server_connection_error']}: {e}")

def render_register():
    with st.container(border=True):
        st.title(_['register'])

        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown("👤")
        with col2:
            name = st.text_input(_['name'], key="reg_name", label_visibility="collapsed")

        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown("📧")
        with col2:
            email = st.text_input(_['email'], key="reg_email", label_visibility="collapsed")

        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown("🔒")
        with col2:
            password = st.text_input(_['password'], type="password", key="reg_pass", label_visibility="collapsed")

        if st.button(_['register']):
            with st.spinner(_['processing']):
                try:
                    response = requests.post(f"{API_URL}/auth/register", json={"name": name, "email": email, "password": password})
                    if response.status_code == 200:
                        st.success(_['register_success'])
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(_['register_error'])
                except requests.exceptions.RequestException as e:
                    st.error(f"{_['server_connection_error']}: {e}")

def render_patient_dashboard():
    st.subheader(_['questionnaire'])
    
    # Check if questionnaires are already loaded
    if not st.session_state.questionnaires:
        with st.spinner(_['processing']):
            try:
                response = requests.get(f"{API_URL}/api/questionnaires")
                if response.status_code == 200:
                    qs = {q['key']: q for q in response.json()}
                    st.session_state.questionnaires = qs
                    st.rerun()
                else:
                    st.error(_['load_questionnaires_error'])
            except requests.exceptions.RequestException as e:
                st.error(f"{_['server_connection_error']}: {e}")
                return # Stop execution if questionnaires can't be loaded
            
    if st.session_state.questionnaires:
        st.subheader("تکمیل پرسشنامه‌ها")
        time_point = st.selectbox("انتخاب زمان", ["t0 (اولیه)", "t1 (یک ماه)", "t2 (سه ماه)"])
        st.session_state.selected_time_point = time_point.split()[0]
        
        for q_key, q_data in st.session_state.questionnaires.items():
            with st.container(border=True):
                st.subheader(q_data[f"title_{st.session_state.locale}"])
                st.write(q_data[f"description_{st.session_state.locale}"]) # Assuming description exists
                if st.button(f"{_['start_form']} - {q_data['key']}", key=f"start_{q_key}"):
                    st.session_state.current_q = q_data
                    st.session_state.form_step = 0
                    st.session_state.page = "form"
                    st.rerun()

    if st.session_state.get('prediction_result'):
        render_prediction_result()

def render_form():
    q_data = st.session_state.current_q
    q_key = q_data['key']
    st.title(q_data[f"title_{st.session_state.locale}"])
    
    questions = q_data['questions']
    total_steps = len(questions)
    
    st.progress(st.session_state.form_step / total_steps)
    
    current_q = questions[st.session_state.form_step]
    
    st.subheader(f"سوال {get_persian_numerals(st.session_state.form_step + 1)} از {get_persian_numerals(total_steps)}")
    st.write(current_q[f"text_{st.session_state.locale}"])
    
    answer_key = f"{q_key}_{current_q['index']}"
    
    if current_q['input_type'] == 'likert_4' or current_q['input_type'] == 'radio':
        options = current_q[f"options_{st.session_state.locale}"]
        selected_option = st.radio(_['choose_one'], options, key=answer_key)
        
    elif current_q['input_type'] == 'yes_no':
        selected_option = st.radio(_['choose_one'], ["بله", "خیر"], key=answer_key)
    
    elif current_q['input_type'] == 'slider_10':
        selected_option = st.slider(_['choose_one'], 0, 10, key=answer_key)

    elif current_q['input_type'] == 'number_input':
        selected_option = st.number_input(_['enter_value'], min_value=0, max_value=120, key=answer_key)

    elif current_q['input_type'] == 'selectbox':
        options = current_q[f"options_{st.session_state.locale}"]
        selected_option = st.selectbox(_['choose_one'], options, key=answer_key)

    elif current_q['input_type'] == 'nmq_bodymap':
        regions = ['گردن', 'شانه‌ها', 'بالای کمر', 'پایین کمر', 'آرنج', 'مچ/دست', 'باسن/ران', 'زانو', 'مچ پا/پا']
        selected_regions = []
        for region in regions:
            if st.checkbox(region, key=f"nmq_{region}"):
                selected_regions.append(region)
        selected_option = selected_regions
    
    st.session_state.form_data[answer_key] = selected_option
    
    if st.button(_['next_step']):
        st.session_state.form_step += 1
        if st.session_state.form_step >= total_steps:
            submit_form()
            st.session_state.form_step = 0
            st.session_state.page = "home"
            st.rerun()

def submit_form():
    user_id = st.session_state.user_info['id']
    q_key = st.session_state.current_q['key']
    q_id = st.session_state.current_q['id']
    time_point = st.session_state.selected_time_point
    
    responses_to_send = []
    # Simplified logic: map stored form data to question IDs
    for q in st.session_state.current_q['questions']:
        answer_key = f"{q_key}_{q['index']}"
        answer = st.session_state.form_data.get(answer_key)
        
        # Simple scoring logic
        if q_key == "phq9":
            score_map = {"اصلا": 0, "چند روزی": 1, "بیش از نیمی از روزها": 2, "تقریبا هر روز": 3}
            answer = score_map.get(answer, 0)
        elif q_key == "rmdq":
            score_map = {"بله": 1, "خیر": 0}
            answer = score_map.get(answer, 0)
            
        responses_to_send.append({
            "question_id": q['id'],
            "answer": answer
        })
    
    payload = {
        "user_id": user_id,
        "questionnaire_id": q_id,
        "time_point": time_point,
        "responses": responses_to_send
    }
    
    with st.spinner(_['processing']):
        try:
            response = requests.post(f"{API_URL}/api/responses", json=payload, headers={"Authorization": f"Bearer {st.session_state.token}"})
            if response.status_code == 200:
                st.success(_['form_submit_success'])
                # Store the calculated score in session state
                if q_key in ["phq9", "rmdq"]: # Example for score storage
                    # This logic needs to be more robust
                    score = sum(r['answer'] for r in responses_to_send)
                    if 'scores' not in st.session_state:
                        st.session_state['scores'] = {}
                    st.session_state['scores'][q_key] = score

                # Call prediction endpoint after T2 or last questionnaire
                if q_key == "rmdq": # A simple trigger for prediction
                    st.session_state.page = "predict_risk"
                    st.rerun()
            else:
                st.error(_['form_submit_error'])
        except requests.exceptions.RequestException as e:
            st.error(f"{_['server_connection_error']}: {e}")

def render_prediction_page():
    st.title(_['risk_prediction'])
    st.write("در حال محاسبه خطر مزمن شدن کمردرد شما...")
    
    # Synthesize all scores from session state to send to the ML model
    scores = st.session_state.get('scores', {})
    patient_data = {
        'fabq_score': scores.get('fabq', 0),
        'phq9_score': scores.get('phq9', 0),
        'pcs_score': scores.get('pcs', 0),
        'tsk11_score': scores.get('tsk11', 0),
        'psqi_score': scores.get('psqi', 0),
        'hplp_score': scores.get('hplp', 0),
        'rmdq_score': scores.get('rmdq', 0),
        'nrs_score': scores.get('nrs', 0),
        'lefs_score': scores.get('lefs', 0),
        'nmq_regions': scores.get('nmq', 0),
    }

    with st.spinner(_['processing']):
        try:
            response = requests.post(f"{API_URL}/api/predict", json={
                "user_id": st.session_state.user_info['id'],
                "time_point": st.session_state.selected_time_point,
                "patient_data": patient_data
            }, headers={"Authorization": f"Bearer {st.session_state.token}"})

            if response.status_code == 200:
                st.session_state.prediction_result = response.json()
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error(_['get_prediction_error'])
        except requests.exceptions.RequestException as e:
            st.error(f"{_['server_connection_error']}: {e}")

def render_prediction_result():
    with st.container(border=True):
        result = st.session_state.prediction_result
        st.title(_['risk_prediction'])

        st.subheader(f"میزان خطر: {get_persian_numerals(result['risk_percentage'])}%")

        if result['risk_percentage'] < 30:
            st.success(f"دسته خطر: {_['risk_category_low']}")
        elif result['risk_percentage'] < 70:
            st.warning(f"دسته خطر: {_['risk_category_moderate']}")
        else:
            st.error(f"دسته خطر: {_['risk_category_high']}")

        st.subheader(_['shap_explanation_title'])
        
        shap_data = result['explanations']
        shap_df = pd.DataFrame(
            {'عامل': list(shap_data.keys()), 'تاثیر': list(shap_data.values())}
        )
        st.bar_chart(shap_df.set_index('عامل'))
        
        if st.button("بازگشت به داشبورد"):
            st.session_state.page = "home"
            st.rerun()

def render_admin_login():
    with st.container(border=True):
        st.title(_['admin_dashboard_title'])
        st.write("لطفاً با حساب کاربری مدیر یا پزشک وارد شوید.")
        email = st.text_input(_['email'], key="admin_email")
        password = st.text_input(_['password'], type="password", key="admin_pass")

        if st.button(_['login']):
            with st.spinner(_['processing']):
                try:
                    response = requests.post(f"{API_URL}/auth/login", json={"username": email, "password": password})
                    if response.status_code == 200:
                        token_data = response.json()
                        if token_data['user_info']['role'] in ["admin", "clinician"]:
                            st.session_state.logged_in = True
                            st.session_state.token = token_data['access_token']
                            st.session_state.user_info = token_data['user_info']
                            st.session_state.page = "admin_dashboard"
                            st.success(_['login_success'])
                            st.rerun()
                        else:
                            st.error(_['unauthorized_access'])
                    else:
                        st.error(_['login_error'])
                except requests.exceptions.RequestException as e:
                    st.error(f"{_['server_connection_error']}: {e}")

def render_admin_dashboard():
    if not st.session_state.logged_in or st.session_state.user_info['role'] not in ["admin", "clinician"]:
        st.error("شما مجوز دسترسی به این بخش را ندارید. لطفاً وارد شوید.")
        st.session_state.page = "admin_login"
        return
        
    st.title(_['admin_dashboard_title'])
    
    # Get analytics data
    with st.spinner(_['processing']):
        try:
            response = requests.get(f"{API_URL}/admin/analytics/overview", headers={"Authorization": f"Bearer {st.session_state.token}"})
            if response.status_code == 200:
                overview = response.json()

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(f"👥 {_['total_patients']}", get_persian_numerals(overview['total_patients']))
                with col2:
                    st.metric(f"⚠️ {_['high_risk_patients']}", get_persian_numerals(overview['patients_with_high_risk']))
                with col3:
                    st.metric(f"📝 {_['avg_phq9']}", get_persian_numerals(overview['average_scores']['phq9']))
                with col4:
                    st.metric(f"📊 {_['avg_nrs']}", get_persian_numerals(overview['average_scores']['nrs']))
            
            # Placeholder for more complex analytics
            st.subheader("توزیع نمرات (نمونه)")
            # Simplified chart data
            chart_data = {
                'NRS Score': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'تعداد بیماران': [5, 15, 20, 30, 25, 15, 10, 5, 3, 2]
            }
            st.bar_chart(chart_data)

        except requests.exceptions.RequestException as e:
            st.error(f"{_['server_connection_error']}: {e}")

# --- Main App Logic ---
page_from_url = st.query_params.get("page")
if page_from_url in ["home", "login", "register", "form", "results", "admin_login", "admin_dashboard", "predict_risk"]:
    st.session_state.page = page_from_url

# Dynamic page routing
if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "login":
    render_login()
elif st.session_state.page == "register":
    render_register()
elif st.session_state.page == "form":
    render_form()
elif st.session_state.page == "predict_risk":
    render_prediction_page()
elif st.session_state.page == "results":
    render_prediction_result()
elif st.session_state.page == "admin_login":
    render_admin_login()
elif st.session_state.page == "admin_dashboard":
    render_admin_dashboard()