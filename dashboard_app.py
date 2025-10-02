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

# -------------------- Survey Questions --------------------
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

# -------------------- Session State --------------------
if "page" not in st.session_state:
    st.session_state.page = "info"
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "show_dashboard" not in st.session_state:
    st.session_state.show_dashboard = False

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

# -------------------- App Layout --------------------
st.set_page_config(page_title="Voice of Industry", layout="wide")
st.title("📝 Voice of Industry Survey & Dashboard")

# -------------------- Survey Flow --------------------
if not st.session_state.show_dashboard:
    if st.session_state.page == "info":
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
                st.error("Please fill all required fields!")
            else:
                st.session_state.responses.update({
                    "name": name,
                    "organization": organization,
                    "org_size": org_size,
                    "org_type": org_type,
                    "location": location
                })
                st.session_state.page = "q1"
                st.rerun()

    elif st.session_state.page in questions:
        qid = st.session_state.page
        qdata = questions[qid]

        st.header(qdata["heading"])
        st.subheader(qdata["question"])
        selected = st.multiselect("Select one or more options:", qdata["options"])

        if st.button("Next ➡️"):
            if not selected:
                st.error("Please select at least one option.")
            else:
                st.session_state.responses[qid] = " || ".join(selected)
                # move to next question or finish
                next_num = int(qid[1]) + 1
                next_page = f"q{next_num}" if f"q{next_num}" in questions else "done"
                st.session_state.page = next_page
                st.rerun()

    elif st.session_state.page == "done":
        save_response(st.session_state.responses)
        st.success("✅ Thank you for completing the survey!")
        if st.button("Go to Dashboard 📊"):
            st.session_state.show_dashboard = True
            st.rerun()

# -------------------- Dashboard --------------------
if st.session_state.show_dashboard:
    st.header("📊 Voice of Industry Dashboard")
    df = load_data()
    if df.empty:
        st.warning("⚠️ No responses yet.")
    else:
        # -------------------- Filters --------------------
        st.sidebar.header("Filters for Dashboard")
        industries = ["All"] + sorted(df["org_type"].dropna().unique().tolist())
        sizes = ["All"] + sorted(df["org_size"].dropna().unique().tolist())
        locations = sorted(df["location"].dropna().unique().tolist())

        selected_industry = st.sidebar.selectbox("Industry Type", industries)
        selected_size = st.sidebar.selectbox("Organization Size", sizes)
        selected_locations = st.sidebar.multiselect("Location (City/Region)", locations)

        filtered_df = df.copy()
        if selected_industry != "All":
            filtered_df = filtered_df[filtered_df["org_type"] == selected_industry]
        if selected_size != "All":
            filtered_df = filtered_df[filtered_df["org_size"] == selected_size]
        if selected_locations:
            filtered_df = filtered_df[filtered_df["location"].isin(selected_locations)]

        # -------------------- KPIs --------------------
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Responses", len(filtered_df))
        kpi2.metric("Unique Organizations", filtered_df["organization"].nunique())
        kpi3.metric("Unique Locations", filtered_df["location"].nunique())

        st.markdown("---")

        # -------------------- Industry Bar --------------------
        st.subheader("🌍 Industry Representation")
        industry_counts = filtered_df["org_type"].value_counts().reset_index()
        industry_counts.columns = ["Industry", "Count"]
        fig_industry = px.bar(industry_counts, x="Industry", y="Count", text="Count", color="Industry")
        st.plotly_chart(fig_industry, use_container_width=True)

        # -------------------- Survey Pie Charts --------------------
        questions_titles = {
            "q1": "The Hiring Hurdle",
            "q2": "The Future Skill Stack",
            "q3": "The First Job Gap",
            "q4": "The Selection Compass",
            "q5": "The Retention Code",
        }

        st.subheader("📊 Survey Insights")
        cols = st.columns(len(questions_titles))
        for idx, (qid, title) in enumerate(questions_titles.items()):
            qdata = filtered_df[qid].dropna()
            with cols[idx]:
                st.markdown(f"#### {title}")
                if not qdata.empty:
                    all_answers = []
                    for row in qdata:
                        all_answers.extend([ans.strip() for ans in row.split("||")])
                    counts = pd.Series(all_answers).value_counts().reset_index()
                    counts.columns = ["Answer", "Count"]

                    fig_pie = px.pie(counts, names="Answer", values="Count", hole=0.3, height=250, width=250)
                    fig_pie.update_layout(
                       
