import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
from geopy.geocoders import Nominatim

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
st.title("📊 Voice of Industry Dashboard")
st.image("logo.png", width=100)

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

# -------------------- KPIs --------------------
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Responses", len(filtered_df))
kpi2.metric("Unique Organizations", filtered_df["organization"].nunique())
kpi3.metric("Unique Locations", filtered_df["location"].nunique())

# -------------------- Layout: Map + Industry Bar --------------------
top_left, top_right = st.columns([1, 1])
with top_left:
    st.subheader("🗺️ Locations")

    @st.cache_data
    def geocode_locations(locations):
        geolocator = Nominatim(user_agent="survey_dashboard")
        coords = []
        for loc in locations:
            try:
                geo = geolocator.geocode(loc)
                if geo:
                    country = None
                    if geo.raw.get("display_name"):
                        parts = geo.raw["display_name"].split(",")
                        country = parts[-1].strip()
                    coords.append({
                        "location": loc,
                        "lat": geo.latitude,
                        "lon": geo.longitude,
                        "country": country
                    })
            except Exception:
                continue
        return pd.DataFrame(coords)

    if not filtered_df["location"].dropna().empty:
        unique_locations = filtered_df["location"].dropna().unique().tolist()
        coords_df = geocode_locations(unique_locations)
        if not coords_df.empty:
            merged = filtered_df.merge(coords_df, on="location", how="left")

            # Decide map scope: India only vs World
            if (coords_df["country"].dropna().nunique() == 1) and \
               (coords_df["country"].dropna().iloc[0].lower() == "india"):
                map_scope = "asia"   # Asia view zooms on India
            else:
                map_scope = "world"

            fig_map = px.scatter_geo(
                merged,
                lat="lat", lon="lon",
                hover_name="organization",
                hover_data=["location", "org_type", "org_size"],
                projection="natural earth",
                scope=map_scope,
                color="org_type",
                height=300
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("⚠️ Could not geocode locations.")
    else:
        st.info("⚠️ No location data available.")

with top_right:
    st.subheader("🌍 Industry Types")
    industry_counts = filtered_df["org_type"].value_counts().reset_index()
    industry_counts.columns = ["Industry Type", "Count"]
    if not industry_counts.empty:
        fig_industry = px.bar(
            industry_counts,
            x="Industry Type", y="Count",
            text="Count", color="Industry Type",
            height=300
        )
        st.plotly_chart(fig_industry, use_container_width=True)

# -------------------- Survey Questions (All Pie Charts in One Row) --------------------
st.subheader("📊 Survey Insights (All Questions)")

questions = {
    "q1": "The Hiring Hurdle",
    "q2": "The Future Skill Stack",
    "q3": "The First Job Gap",
    "q4": "The Selection Compass",
    "q5": "The Retention Code",
}

# Create 5 equal columns (one per chart)
cols = st.columns(len(questions))

for idx, (qid, title) in enumerate(questions.items()):
    qdata = filtered_df[qid].dropna()
    with cols[idx]:
        st.markdown(f"#### {title}")  # Title above chart
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
            # Legend below chart (horizontal)
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

# -------------------- Raw Data --------------------
with st.expander("📂 Raw Survey Data (Filtered)"):
    st.dataframe(filtered_df, use_container_width=True, height=250)
    st.download_button(
        "⬇️ Download CSV",
        filtered_df.to_csv(index=False),
        "survey_responses_filtered.csv",
        "text/csv"
    )
