import streamlit as st
import requests
import json
from streamlit.components.v1 import html
from datetime import datetime
import time

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
    st.markdown(
        f"""
        <div class="top-bar">
            <div class="top-bar-right">
                <a href="/?page=admin_login" target="_self">
                    <button style="border:none; background:none; cursor:pointer;">
                        {_['admin_link']}
                    </button>
                </a>
                <span style="margin: 0 10px;">|</span>
                <button onclick="window.location.href = '/?page=home'" style="border:none; background:none; cursor:pointer;">
                    {_['app_name']}
                </button>
            </div>
            <div class="top-bar-left">
                <button style="border:none; background:none; cursor:pointer;" onclick="window.location.href = '/?page=lang_toggle'">
                    {_['lang_toggle']}
                </button>
                <span style="margin: 0 10px;">|</span>
                <button style="border:none; background:none; cursor:pointer;" onclick="window.location.href = '/?page=num_toggle'">
                    {_['persian_numerals_toggle']}
                </button>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def handle_lang_toggle():
    if st.session_state.page == "lang_toggle":
        st.session_state['locale'] = 'en' if st.session_state['locale'] == 'fa' else 'fa'
        st.session_state.page = "home" # Redirect to home to apply change
        st.experimental_rerun()
    elif st.session_state.page == "num_toggle":
        st.session_state.persian_numerals = not st.session_state.persian_numerals
        st.session_state.page = "home"
        st.experimental_rerun()

handle_lang_toggle()
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
                st.experimental_rerun()
        with col2:
            if st.button(_['register']):
                st.session_state.page = "register"
                st.experimental_rerun()
    else:
        st.subheader(f"👋 {st.session_state.user_info['name']}، خوش آمدید!")
        if st.session_state.user_info['role'] == "patient":
            render_patient_dashboard()
        else:
            st.warning("Only patients have a dashboard.")

def render_login():
    st.title(_['login'])
    email = st.text_input(_['email'], key="login_email")
    password = st.text_input(_['password'], type="password", key="login_pass")
    if st.button(_['login']):
        try:
            response = requests.post(f"{API_URL}/auth/login", json={"username": email, "password": password})
            if response.status_code == 200:
                token_data = response.json()
                st.session_state.logged_in = True
                st.session_state.token = token_data['access_token']
                st.session_state.user_info = token_data['user_info']
                st.session_state.page = "home"
                st.success("ورود موفقیت‌آمیز بود! در حال انتقال...")
                time.sleep(1)
                st.experimental_rerun()
            else:
                st.error("اطلاعات کاربری اشتباه است.")
        except requests.exceptions.RequestException as e:
            st.error(f"خطا در ارتباط با سرور: {e}")

def render_register():
    st.title(_['register'])
    name = st.text_input(_['name'], key="reg_name")
    email = st.text_input(_['email'], key="reg_email")
    password = st.text_input(_['password'], type="password", key="reg_pass")
    if st.button(_['register']):
        try:
            response = requests.post(f"{API_URL}/auth/register", json={"name": name, "email": email, "password": password})
            if response.status_code == 200:
                st.success("ثبت‌نام موفقیت‌آمیز بود! اکنون وارد شوید.")
                st.session_state.page = "login"
                st.experimental_rerun()
            else:
                st.error("خطا در ثبت‌نام. لطفا دوباره تلاش کنید.")
        except requests.exceptions.RequestException as e:
            st.error(f"خطا در ارتباط با سرور: {e}")

def render_patient_dashboard():
    st.subheader(_['questionnaire'])
    
    # Check if questionnaires are already loaded
    if not st.session_state.questionnaires:
        try:
            response = requests.get(f"{API_URL}/api/questionnaires")
            if response.status_code == 200:
                qs = {q['key']: q for q in response.json()}
                st.session_state.questionnaires = qs
            else:
                st.error("Failed to load questionnaires.")
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
            
    if st.session_state.questionnaires:
        st.subheader("تکمیل پرسشنامه‌ها")
        time_point = st.selectbox("انتخاب زمان", ["t0 (اولیه)", "t1 (یک ماه)", "t2 (سه ماه)"])
        st.session_state.selected_time_point = time_point.split()[0]
        
        for q_key, q_data in st.session_state.questionnaires.items():
            st.subheader(q_data[f"title_{st.session_state.locale}"])
            if st.button(f"{_['start_form']} - {q_data['key']}", key=f"start_{q_key}"):
                st.session_state.current_q = q_data
                st.session_state.form_step = 0
                st.session_state.page = "form"
                st.experimental_rerun()

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
    
    if current_q['input_type'] == 'likert_4':
        options = current_q[f"options_{st.session_state.locale}"]
        selected_option = st.radio("انتخاب کنید:", options, key=answer_key)
        
    elif current_q['input_type'] == 'yes_no':
        selected_option = st.radio("انتخاب کنید:", ["بله", "خیر"], key=answer_key)
    
    elif current_q['input_type'] == 'slider_10':
        selected_option = st.slider("انتخاب کنید:", 0, 10, key=answer_key)

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
            st.experimental_rerun()

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
    
    try:
        response = requests.post(f"{API_URL}/api/responses", json=payload, headers={"Authorization": f"Bearer {st.session_state.token}"})
        if response.status_code == 200:
            st.success("پاسخ‌ها با موفقیت ثبت شد!")
            # Call prediction endpoint after T2 or last questionnaire
            if q_key == "rmdq": # A simple trigger for prediction
                st.session_state.page = "predict_risk"
                st.experimental_rerun()
        else:
            st.error("خطا در ثبت پاسخ‌ها.")
    except requests.exceptions.RequestException as e:
        st.error(f"خطا در ارتباط با سرور: {e}")

def render_prediction_page():
    st.title(_['risk_prediction'])
    st.write("در حال محاسبه خطر مزمن شدن کمردرد شما...")
    
    # Synthesize all scores to send to the ML model
    patient_data = {
        'fabq_score': 50, # Example placeholder
        'phq9_score': 12,
        'pcs_score': 35,
        'tsk11_score': 30,
        'psqi_score': 8,
        'hplp_score': 120,
        'rmdq_score': 15,
        'nrs_score': 7,
        'lefs_score': 45,
        'nmq_regions': 3,
    }

    try:
        response = requests.post(f"{API_URL}/api/predict", json={
            "user_id": st.session_state.user_info['id'],
            "time_point": st.session_state.selected_time_point,
            "patient_data": patient_data
        }, headers={"Authorization": f"Bearer {st.session_state.token}"})
        
        if response.status_code == 200:
            st.session_state.prediction_result = response.json()
            st.session_state.page = "results"
            st.experimental_rerun()
        else:
            st.error("خطا در دریافت پیش‌بینی از سرور.")
    except requests.exceptions.RequestException as e:
        st.error(f"خطا در ارتباط با سرور: {e}")
        
def render_prediction_result():
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
        st.experimental_rerun()

def render_admin_login():
    st.title(_['admin_dashboard_title'])
    st.write("لطفاً با حساب کاربری مدیر یا پزشک وارد شوید.")
    email = st.text_input(_['email'], key="admin_email")
    password = st.text_input(_['password'], type="password", key="admin_pass")
    
    if st.button(_['login']):
        try:
            response = requests.post(f"{API_URL}/auth/login", json={"username": email, "password": password})
            if response.status_code == 200:
                token_data = response.json()
                if token_data['user_info']['role'] in ["admin", "clinician"]:
                    st.session_state.logged_in = True
                    st.session_state.token = token_data['access_token']
                    st.session_state.user_info = token_data['user_info']
                    st.session_state.page = "admin_dashboard"
                    st.success("ورود به پنل مدیریت موفقیت‌آمیز بود.")
                    st.experimental_rerun()
                else:
                    st.error("شما مجوز دسترسی به این بخش را ندارید.")
            else:
                st.error("اطلاعات کاربری اشتباه است.")
        except requests.exceptions.RequestException as e:
            st.error(f"خطا در ارتباط با سرور: {e}")

def render_admin_dashboard():
    if not st.session_state.logged_in or st.session_state.user_info['role'] not in ["admin", "clinician"]:
        st.error("شما مجوز دسترسی به این بخش را ندارید. لطفاً وارد شوید.")
        st.session_state.page = "admin_login"
        return
        
    st.title(_['admin_dashboard_title'])
    
    # Get analytics data
    try:
        response = requests.get(f"{API_URL}/admin/analytics/overview", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if response.status_code == 200:
            overview = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(_['total_patients'], get_persian_numerals(overview['total_patients']))
            with col2:
                st.metric(_['high_risk_patients'], get_persian_numerals(overview['patients_with_high_risk']))
            with col3:
                st.metric(_['avg_phq9'], get_persian_numerals(overview['average_scores']['phq9']))
            with col4:
                st.metric(_['avg_nrs'], get_persian_numerals(overview['average_scores']['nrs']))
        
        # Placeholder for more complex analytics
        st.subheader("توزیع نمرات (نمونه)")
        # Simplified chart data
        chart_data = {
            'NRS Score': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'تعداد بیماران': [5, 15, 20, 30, 25, 15, 10, 5, 3, 2]
        }
        st.bar_chart(chart_data)

    except requests.exceptions.RequestException as e:
        st.error(f"خطا در دریافت داده‌های تحلیلی: {e}")

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