import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text

# -------------------- Database Path --------------------
DB_FILE = os.path.join(os.path.dirname(__file__), "survey_responses.db")
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

# Ensure table exists
with engine.begin() as conn:
    conn.execute(text("""
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
    """))

# -------------------- Streamlit Config --------------------
st.set_page_config(page_title="Voice of Industry Survey", layout="centered")
st.title("📝 Voice of Industry Survey")

# -------------------- Survey Form --------------------
with st.form("survey_form", clear_on_submit=True):
    name = st.text_input("Your Name")
    organization = st.text_input("Organization")
    org_size = st.selectbox("Organization Size", ["Small", "Medium", "Large"])
    org_type = st.text_input("Organization Type (e.g., IT, Finance, Manufacturing)")
    location = st.text_input("City/Region")

    q1 = st.multiselect("The Hiring Hurdle - Roadblock in hiring fresh graduates",
                        ["Poor communication and confidence",
                         "Weak problem-solving ability",
                         "Unrealistic salary or role expectations",
                         "Lack of workplace readiness (discipline, etiquette, basics)",
                         "Shallow domain knowledge"])

    q2 = st.multiselect("The Future Skill Stack - Skills that matter in next 5 years",
                        ["AI/ML", "Data Analytics", "Cloud Computing",
                         "Cybersecurity", "Soft Skills", "Domain Knowledge"])

    q3 = st.multiselect("The First Job Gap - Gap between expectation and reality",
                        ["Work culture shock", "Skill mismatch",
                         "Teamwork & collaboration issues", "Unrealistic expectations"])

    q4 = st.multiselect("The Selection Compass - Trait to bet on when hiring",
                        ["Problem solving", "Adaptability",
                         "Communication skills", "Teamwork", "Integrity"])

    q5 = st.multiselect("The Retention Code - Retaining young talent in first 2 years",
                        ["Career growth opportunities", "Work-life balance",
                         "Learning & development", "Compensation", "Mentorship"])

    submitted = st.form_submit_button("✅ Submit Response")

    if submitted:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO responses
                (name, organization, org_size, org_type, location, q1, q2, q3, q4, q5)
                VALUES (:name, :organization, :org_size, :org_type, :location, :q1, :q2, :q3, :q4, :q5)
            """), {
                "name": name,
                "organization": organization,
                "org_size": org_size,
                "org_type": org_type,
                "location": location,
                "q1": "||".join(q1),
                "q2": "||".join(q2),
                "q3": "||".join(q3),
                "q4": "||".join(q4),
                "q5": "||".join(q5)
            })

        st.success("🎉 Thank you! Your response has been recorded.")
        st.rerun()  # 🔑 ensures instant dashboard refresh

# -------------------- Page: Completion --------------------
elif st.session_state.page == "done":
    save_response(st.session_state.responses)
    st.success("✅ Thank you for completing the survey!")
    st.markdown("You can now view the **live dashboard** [here](http://localhost:8502)")
    st.balloons()
    st.stop()

