import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# -------------------- DB Connection --------------------
DB_URL = st.secrets["SUPABASE_DB_URL"]
engine = create_engine(DB_URL)

# -------------------- Survey Questions --------------------
questions = {
    "q1": {"heading": "The Hiring Hurdle",
           "question": "What is the single biggest roadblock you face in hiring fresh graduates?",
           "options": [
               "Poor communication and confidence",
               "Weak problem-solving ability",
               "Unrealistic salary or role expectations",
               "Lack of workplace readiness",
               "Shallow domain knowledge"
           ]},
    "q2": {"heading": "The Future Skill Stack",
           "question": "Which skills will matter most for young professionals in the next 5 years?",
           "options": [
               "Digital & data literacy",
               "Problem solving & analytical thinking",
               "Financial & business acumen",
               "Communication & collaboration",
               "Adaptability & agility"
           ]},
    "q3": {"heading": "The First Job Gap",
           "question": "When freshers join, where do you see the biggest gap between expectation and reality?",
           "options": [
               "Workplace behavior / professionalism",
               "Ability to apply knowledge in practice",
               "Confidence & communication",
               "Discipline & work ethic",
               "Ownership / accountability"
           ]},
    "q4": {"heading": "The Selection Compass",
           "question": "If you could pick only one trait while hiring, which would you bet on?",
           "options": [
               "Attitude & learnability",
               "Integrity & ethics",
               "Communication skills",
               "Resilience & work ethic",
               "Domain knowledge"
           ]},
    "q5": {"heading": "The Retention Code",
           "question": "What matters most in retaining young talent in the first 2 years?",
           "options": [
               "Growth & learning opportunities",
               "Good manager and team culture",
               "Competitive compensation",
               "Work-life balance & flexibility",
               "Role alignment with skills"
           ]}
}

if "page" not in st.session_state:
    st.session_state.page = "info"
if "responses" not in st.session_state:
    st.session_state.responses = {}

# -------------------- Save Function --------------------
def save_response(data):
    with engine.begin() as conn:
        conn.execute(text("""
            insert into responses
            (name, organization, org_size, org_type, location, q1, q2, q3, q4, q5)
            values (:name, :organization, :org_size, :org_type, :location, :q1, :q2, :q3, :q4, :q5)
        """), data)

# -------------------- UI --------------------
st.set_page_config(page_title="Voice of Industry Survey", layout="wide")
st.title("📝 Voice of Industry Survey")

# Page 1: Info
if st.session_state.page == "info":
    st.header("Respondent Information")
    name = st.text_input("Full Name")
    organization = st.text_input("Organization Name")
    org_size = st.radio("Organization Size", ["<50", "51-100", "101-250", "250+"])
    org_type = st.selectbox("Type of Organization", [
        "Agriculture & Farming", "Manufacturing & Industrial", "Construction & Real Estate",
        "Information Technology (IT & Software)", "Healthcare & Pharmaceuticals",
        "Banking, Finance & Insurance", "Education & Training", "Tourism & Hospitality",
        "Transport & Logistics", "Media & Entertainment", "Energy & Power",
        "Retail & E-commerce", "Others"
    ])
    location = st.text_input("City / Region")

    if st.button("Next"):
        if not name or not organization or not location:
            st.error("Please fill all required fields!")
        else:
            st.session_state.responses.update({
                "name": name, "organization": organization,
                "org_size": org_size, "org_type": org_type, "location": location
            })
            st.session_state.page = "q1"

# Pages: Questions
elif st.session_state.page in questions:
    qid = st.session_state.page
    qdata = questions[qid]
    st.header(qdata["heading"])
    st.subheader(qdata["question"])
    selected = st.multiselect("Select one or more options:", qdata["options"])

    if st.button("Next"):
        if not selected:
            st.error("Please select at least one option.")
        else:
            st.session_state.responses[qid] = " || ".join(selected)
            next_num = int(qid[1]) + 1
            st.session_state.page = f"q{next_num}" if f"q{next_num}" in questions else "done"

# Page: Done
elif st.session_state.page == "done":
    save_response(st.session_state.responses)
    st.success("✅ Thank you for completing the survey!")
