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
    "q1": ("The Hiring Hurdle", 
           "What is the single biggest roadblock you face when hiring fresh graduates?", 
           ["Poor communication and confidence","Weak problem-solving ability","Unrealistic salary or role expectations","Lack of workplace readiness","Shallow domain knowledge"]),
    "q2": ("The Future Skill Stack", 
           "Which skills will matter most for young professionals in the next 5 years?", 
           ["Digital & data literacy","Problem solving & analytical thinking","Financial & business acumen","Communication & collaboration","Adaptability & agility"]),
    "q3": ("The First Job Gap", 
           "When freshers join, where do you see the biggest gap between expectation and reality?", 
           ["Workplace behavior","Ability to apply knowledge in practice","Confidence & communication","Discipline & work ethic","Ownership / accountability"]),
    "q4": ("The Selection Compass", 
           "If you could pick only one trait while hiring, which would you bet on?", 
           ["Attitude & learnability","Integrity & ethics","Communication skills","Resilience & work ethic","Domain knowledge"]),
    "q5": ("The Retention Code", 
           "What matters most in retaining young talent in the first 2 years?", 
           ["Growth & learning opportunities","Good manager and team culture","Competitive compensation","Work-life balance & flexibility","Role alignment with skills"]),
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
        data["name"], data["organization"], data["org_size"], data["org_type"], data["location"],
        data["q1"], data["q2"], data["q3"], data["q4"], data["q5"]
    ))
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM responses", conn)
    conn.close()
    return df

# -------------------- Sidebar Navigation --------------------
st.set_page_config(page_title="Voice of Industry", layout="wide")
st.sidebar.title("🔍 Navigation")
page = st.sidebar.radio("Go to", ["Survey", "Dashboard"])

# -------------------- Survey Page --------------------
if page == "Survey":
    st.title("📝 Voice of Industry Survey")

    # Respondent info
    name = st.text_input("Full Name")
    organization = st.text_input("Organization Name")
    org_size = st.radio("Organization Size", ["<50", "51-100", "101-250", "250+"])
    org_type = st.selectbox("Type of Organization",
        ["Agriculture & Farming","Manufacturing & Industrial","Construction & Real Estate",
         "Information Technology (IT & Software)","Healthcare & Pharmaceuticals",
         "Banking, Finance & Insurance","Education & Training","Tourism & Hospitality",
         "Transport & Logistics","Media & Entertainment","Energy & Power","Retail & E-commerce","Others"])
    location = st.text_input("City / Region")

    responses = {"name": name, "organization": organization, "org_size": org_size,
                 "org_type": org_type, "location": location}

    # Survey questions
    for qid, (heading, question, options) in questions.items():
        st.subheader(heading)
        st.write(question)
        selected = st.multiselect("Select one or more options:", options, key=qid)
        responses[qid] = " || ".join(selected)

    if st.button("Submit Survey"):
        if not name or not organization or not location:
            st.error("⚠️ Please fill all required fields.")
        else:
            save_response(responses)
            st.success("✅ Thank you for completing the survey!")
            st.balloons()

# -------------------- Dashboard Page --------------------
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

    # Pie charts in one row
    st.subheader("Survey Insights")
    cols = st.columns(len(questions))
    for idx, (qid, (heading, _, _)) in enumerate(questions.items()):
        qdata = df[qid].dropna()
        with cols[idx]:
            st.markdown(f"#### {heading}")
            if not qdata.empty:
                all_answers = []
                for row in qdata:
                    all_answers.extend([ans.strip() for ans in row.split("||")])
                answer_counts = pd.Series(all_answers).value_counts().reset_index()
                answer_counts.columns = ["Answer", "Count"]
                fig = px.pie(answer_counts, names="Answer", values="Count", hole=0.4)
                fig.update_layout(
                    legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"),
                    margin=dict(t=30, b=40, l=10, r=10)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No responses yet.")

    st.markdown("---")

    # Raw Data
    with st.expander("📂 View Raw Data"):
        st.dataframe(df, use_container_width=True)
