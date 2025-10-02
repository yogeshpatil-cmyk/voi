import streamlit as st
import sqlite3
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
# -------------------- Database Setup --------------------
DB_FILE = os.path.join(os.path.dirname(__file__), "survey_responses.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        organization TEXT,
        org_size TEXT,
        org_type TEXT,
        location TEXT,
        q1 TEXT,
        q2 TEXT,
        q3 TEXT,
        q4 TEXT,
        q5 TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------- Questions --------------------
questions = {
    "q1": {
        "heading": "The Hiring Hurdle",
        "question": "What is the single biggest roadblock you face when hiring fresh graduates?",
        "options": [
            "Poor communication and confidence",
            "Weak problem-solving ability",
            "Unrealistic salary or role expectations",
            "Lack of workplace readiness",
            "Shallow domain knowledge"
        ]
    },
    "q2": {
        "heading": "The Future Skill Stack",
        "question": "Which skills will matter most for young professionals in the next 5 years?",
        "options": [
            "Digital & data literacy",
            "Problem solving & analytical thinking",
            "Financial & business acumen",
            "Communication & collaboration",
            "Adaptability & agility"
        ]
    },
    "q3": {
        "heading": "The First Job Gap",
        "question": "When freshers join, where do you see the biggest gap between expectation and reality?",
        "options": [
            "Workplace behavior / professionalism",
            "Ability to apply knowledge in practice",
            "Confidence & communication",
            "Discipline & work ethic",
            "Ownership / accountability"
        ]
    },
    "q4": {
        "heading": "The Selection Compass",
        "question": "If you could pick only one trait while hiring, which would you bet on?",
        "options": [
            "Attitude & learnability",
            "Integrity & ethics",
            "Communication skills",
            "Resilience & work ethic",
            "Domain knowledge"
        ]
    },
    "q5": {
        "heading": "The Retention Code",
        "question": "What matters most in retaining young talent in the first 2 years?",
        "options": [
            "Growth & learning opportunities",
            "Good manager and team culture",
            "Competitive compensation",
            "Work-life balance & flexibility",
            "Role alignment with skills"
        ]
    },
}

# -------------------- Functions --------------------
def save_response(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO responses 
        (name, organization, org_size, org_type, location, q1, q2, q3, q4, q5)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name"), data.get("organization"), data.get("org_size"),
        data.get("org_type"), data.get("location"),
        data.get("q1"), data.get("q2"), data.get("q3"),
        data.get("q4"), data.get("q5")
    ))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM responses", conn)
    conn.close()
    return df

# -------------------- Sidebar --------------------
st.set_page_config(page_title="Voice of Industry", layout="wide")
page = st.sidebar.radio("Go to", ["Survey", "Dashboard"])

# -------------------- Survey --------------------
if page == "Survey":
    st.title("📝 Voice of Industry Survey")

    # Initialize session state
    if "survey_page" not in st.session_state:
        st.session_state.survey_page = "info"
    if "responses" not in st.session_state:
        st.session_state.responses = {}

    # Page: Respondent Info
    if st.session_state.survey_page == "info":
        st.header("Respondent Information")
        name = st.text_input("Full Name")
        organization = st.text_input("Organization Name")
        org_size = st.radio("Organization Size", ["<50", "51-100", "101-250", "250+"])
        org_type = st.selectbox(
            "Type of Organization",
            ["Agriculture & Farming","Manufacturing & Industrial","Construction & Real Estate",
             "Information Technology (IT & Software)","Healthcare & Pharmaceuticals",
             "Banking, Finance & Insurance","Education & Training","Tourism & Hospitality",
             "Transport & Logistics","Media & Entertainment","Energy & Power","Retail & E-commerce","Others"]
        )
        location = st.text_input("City / Region")

        if st.button("Start Survey ➡️"):
            if not name or not organization or not location:
                st.error("Please fill all required fields.")
            else:
                st.session_state.responses.update({
                    "name": name,
                    "organization": organization,
                    "org_size": org_size,
                    "org_type": org_type,
                    "location": location,
                    })
                st.session_state.survey_page = "q1"
                st.experimental_rerun()

    # Pages: Questions
    elif st.session_state.survey_page in questions:
        qid = st.session_state.survey_page
        qdata = questions[qid]
        st.header(qdata["heading"])
        st.write(qdata["question"])
        selected = st.multiselect("Select one or more options:", qdata["options"], key=qid)

    if st.button("Next ➡️"):
    if not selected:
        st.error("Please select at least one option.")
    else:
        st.session_state.responses[qid] = " || ".join(selected)
        next_q = f"q{int(qid[1]) + 1}"
        if next_q in questions:
            st.session_state.survey_page = next_q
        else:
            st.session_state.survey_page = "done"


    # Page: Completion
    elif st.session_state.survey_page == "done":
        save_response(st.session_state.responses)
        st.success("✅ Thank you for completing the survey!")
        st.balloons()
        st.session_state.survey_page = "info"  # Reset for next respondent

# -------------------- Dashboard --------------------
elif page == "Dashboard":
    st.title("📊 Voice of Industry Dashboard")
    df = load_data()

    if df.empty:
        st.warning("⚠️ No responses yet.")
        st.stop()

    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Responses", len(df))
    col2.metric("Unique Organizations", df["organization"].nunique())
    col3.metric("Unique Locations", df["location"].nunique())

    st.markdown("---")

    # Pie charts
    st.subheader("Survey Insights")
    cols = st.columns(len(questions))
    for idx, (qid, qdata) in enumerate(questions.items()):
        with cols[idx]:
            st.markdown(f"#### {qdata['heading']}")
            qdata_series = df[qid].dropna()
            if not qdata_series.empty:
                all_answers = []
                for row in qdata_series:
                    all_answers.extend([ans.strip() for ans in row.split("||")])
                counts = pd.Series(all_answers).value_counts().reset_index()
                counts.columns = ["Answer", "Count"]
                fig = px.pie(counts, names="Answer", values="Count", hole=0.4)
                fig.update_layout(
                    legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"),
                    margin=dict(t=30, b=40, l=10, r=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No responses yet.")

