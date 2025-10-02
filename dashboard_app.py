import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import os

st.set_page_config(page_title="Voice of Industry Dashboard", layout="wide")
st.image("logo.png", width=100)
st.title("📊 Voice of Industry Dashboard")

# -------------------- DATABASE CONNECTION --------------------
# Try Supabase first
DB_URL = st.secrets.get("SUPABASE_DB_URL") or os.getenv("SUPABASE_DB_URL")

# Add SSL for Supabase
if DB_URL and "postgresql://" in DB_URL:
    if "?sslmode=" not in DB_URL:
        DB_URL += "?sslmode=require"

use_sqlite = False
if not DB_URL:
    st.warning("⚠️ Supabase DB not configured. Using local SQLite fallback.")
    DB_URL = "sqlite:///survey_responses.db"
    use_sqlite = True

try:
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False} if use_sqlite else {}
    )
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# -------------------- LOAD DATA --------------------
@st.cache_data
def load_data():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM responses ORDER BY submitted_at DESC"))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        return df
    except Exception as e:
        st.warning(f"No data found or table missing: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("⚠️ No responses yet.")
    st.stop()

# -------------------- QUESTIONS --------------------
questions = {
    "q1": "The Hiring Hurdle",
    "q2": "The Future Skill Stack",
    "q3": "The First Job Gap",
    "q4": "The Selection Compass",
    "q5": "The Retention Code",
}

# -------------------- Survey Insights --------------------
st.subheader("📊 Survey Insights")
cols = st.columns(len(questions))
for idx, (qid, title) in enumerate(questions.items()):
    qdata = df[qid].dropna() if qid in df.columns else pd.Series()
    with cols[idx]:
        st.markdown(f"#### {title}")
        if not qdata.empty:
            all_answers = []
            for row in qdata:
                all_answers.extend([ans.strip() for ans in str(row).split("||")])
            answer_counts = pd.Series(all_answers).value_counts().reset_index()
            answer_counts.columns = ["Answer", "Count"]
            fig_pie = px.pie(
                answer_counts, names="Answer", values="Count",
                hole=0.4, height=250, width=250
            )
            fig_pie.update_layout(
                legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center", font=dict(size=9)),
                margin=dict(t=30, b=40, l=10, r=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No data for this question yet.")

# -------------------- KPIs + Industry Distribution --------------------
st.subheader("📈 Key Metrics & Industry Distribution")
kpi_col, chart_col = st.columns([1, 2])
with kpi_col:
    st.metric("Total Responses", len(df))
    st.metric("Unique Organizations", df["organization"].nunique() if "organization" in df.columns else 0)
    st.metric("Unique Locations", df["location"].nunique() if "location" in df.columns else 0)

with chart_col:
    if "org_type" in df.columns and not df["org_type"].isna().all():
        industry_counts = df["org_type"].value_counts().reset_index()
        industry_counts.columns = ["Industry Type", "Count"]
        fig_industry = px.bar(
            industry_counts, x="Industry Type", y="Count",
            text="Count", color="Industry Type", height=300
        )
        st.plotly_chart(fig_industry, use_container_width=True)
    else:
        st.info("No organization type data available.")

# -------------------- Raw Data --------------------
with st.expander("📂 Raw Survey Data"):
    st.dataframe(df, use_container_width=True, height=250)
    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False),
        "survey_responses.csv",
        "text/csv"
    )
