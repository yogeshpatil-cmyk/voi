import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# -------------------- Database Connection --------------------
DB_FILE = "survey_responses.db"
engine = create_engine(f"sqlite:///{DB_FILE}")

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
st.set_page_config(page_title="Voice of Industry Dashboard", layout="wide")

# -------------------- Load Data --------------------
@st.cache_data
def load_data():
    return pd.read_sql("SELECT * FROM responses", engine)

df = load_data()

if df.empty:
    st.warning("⚠️ No responses yet.")
    st.stop()

# -------------------- Filters --------------------
st.sidebar.header("🔍 Filters")
industry_options = ["All"] + sorted(df["org_type"].dropna().unique().tolist())
size_options = ["All"] + sorted(df["org_size"].dropna().unique().tolist())
location_options = sorted(df["location"].dropna().unique().tolist())

selected_industry = st.sidebar.selectbox("Industry Type", industry_options)
selected_size = st.sidebar.selectbox("Organization Size", size_options)
selected_locations = st.sidebar.multiselect("Location (City/Region)", location_options)

filtered_df = df.copy()
if selected_industry != "All":
    filtered_df = filtered_df[filtered_df["org_type"] == selected_industry]
if selected_size != "All":
    filtered_df = filtered_df[filtered_df["org_size"] == selected_size]
if selected_locations:
    filtered_df = filtered_df[filtered_df["location"].isin(selected_locations)]

# -------------------- First Row: Logo + Title + KPI --------------------
col_logo, col_title, col_kpi = st.columns([1, 5, 2])

with col_logo:
    st.image("logo.png", width=80)

with col_title:
    st.markdown(
        "<h1 style='text-align:center; margin-top: 10px;'>📊 Voice of Industry Dashboard</h1>",
        unsafe_allow_html=True
    )

with col_kpi:
    st.markdown(
        f"""
        <div style="text-align:right;">
            <div style="font-size:22px; font-weight:bold; margin-bottom:5px;">
                Total Responses
            </div>
            <div style="font-size:34px; color:#2E86C1; font-weight:bold;">
                {len(filtered_df)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------- Second Row: Pie Charts --------------------
questions = {
    "q1": "The Hiring Hurdle",
    "q2": "The Future Skill Stack",
    "q3": "The First Job Gap",
    "q4": "The Selection Compass",
    "q5": "The Retention Code",
}

cols = st.columns(len(questions))

for idx, (qid, title) in enumerate(questions.items()):
    qdata = filtered_df[qid].dropna()
    with cols[idx]:
        st.markdown(f"#### {title}")
        if not qdata.empty:
            all_answers = []
            for row in qdata:
                all_answers.extend([ans.strip() for ans in row.split("||")])
            answer_counts = pd.Series(all_answers).value_counts().reset_index()
            answer_counts.columns = ["Answer", "Count"]

            fig_pie = px.pie(
                answer_counts,
                names="Answer",
                values="Count",
                hole=0.4,
                height=280,
                width=280
            )
            fig_pie.update_layout(
                legend=dict(
                    orientation="h",
                    y=-0.3,
                    x=0.5,
                    xanchor="center",
                    font=dict(size=9)
                ),
                margin=dict(t=30, b=40, l=10, r=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info(f"No responses yet for {title}.")

# -------------------- Third Row: Industry Bar Chart --------------------
st.subheader("🌍 Industry Types")
industry_counts = filtered_df["org_type"].value_counts().reset_index()
industry_counts.columns = ["Industry Type", "Count"]
if not industry_counts.empty:
    fig_industry = px.bar(
        industry_counts,
        x="Industry Type", y="Count",
        text="Count", color="Industry Type",
        height=400
    )
    st.plotly_chart(fig_industry, use_container_width=True)

# -------------------- Raw Data --------------------
with st.expander("📂 Raw Survey Data (Filtered)"):
    st.dataframe(filtered_df, use_container_width=True, height=250)
    st.download_button(
        "⬇️ Download CSV",
        filtered_df.to_csv(index=False),
        "survey_responses_filtered.csv",
        "text/csv"
    )
