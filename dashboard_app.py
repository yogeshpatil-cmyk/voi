import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

DB_URL = st.secrets["SUPABASE_DB_URL"]
engine = create_engine(DB_URL)

st.set_page_config(page_title="Voice of Industry Dashboard", layout="wide")
st.title("📊 Voice of Industry Dashboard")

@st.cache_data
def load_data():
    return pd.read_sql("select * from responses order by submitted_at desc", engine)

df = load_data()

if df.empty:
    st.warning("⚠️ No responses yet.")
    st.stop()

questions = {
    "q1": "The Hiring Hurdle",
    "q2": "The Future Skill Stack",
    "q3": "The First Job Gap",
    "q4": "The Selection Compass",
    "q5": "The Retention Code",
}

# Survey Insights
st.subheader("📊 Survey Insights")
cols = st.columns(len(questions))
for idx, (qid, title) in enumerate(questions.items()):
    qdata = df[qid].dropna()
    with cols[idx]:
        st.markdown(f"#### {title}")
        if not qdata.empty:
            all_answers = []
            for row in qdata:
                all_answers.extend([ans.strip() for ans in row.split("||")])
            answer_counts = pd.Series(all_answers).value_counts().reset_index()
            answer_counts.columns = ["Answer", "Count"]
            fig_pie = px.pie(answer_counts, names="Answer", values="Count", hole=0.4, height=250, width=250)
            st.plotly_chart(fig_pie, use_container_width=True)

# KPIs
st.subheader("📈 Key Metrics & Industry Distribution")
kpi_col, chart_col = st.columns([1, 2])
with kpi_col:
    st.metric("Total Responses", len(df))
with chart_col:
    industry_counts = df["org_type"].value_counts().reset_index()
    industry_counts.columns = ["Industry Type", "Count"]
    fig_industry = px.bar(industry_counts, x="Industry Type", y="Count", text="Count", color="Industry Type", height=300)
    st.plotly_chart(fig_industry, use_container_width=True)

# Raw Data
with st.expander("📂 Raw Survey Data"):
    st.dataframe(df, use_container_width=True, height=250)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False), "survey_responses.csv", "text/csv")