import os
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

# --- Page Setup ---
st.set_page_config(
    page_title="WildWing | Avian Field Intelligence",
    page_icon="🌿",
    layout="wide",
)

# Shared chart styling theme
CHART_THEME = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "margin": dict(l=20, r=20, t=40, b=20),
}


# --- Data Pipeline ---
def find_database_path() -> str:
  base_dir = os.path.dirname(os.path.abspath(__file__))
  candidate_paths = [
      os.path.join(base_dir, "bird_monitoring.db"),
      os.path.join(base_dir, "data", "bird_monitoring.db"),
      os.path.join(os.path.abspath(os.path.join(base_dir, "..")), "data", "bird_monitoring.db"),
  ]
  for path in candidate_paths:
    if os.path.exists(path):
      return path
  return ""


@st.cache_data(show_spinner="Gathering field survey logs...")
def load_survey_data():
  db_path = find_database_path()
  if not db_path:
    st.error("Couldn't find `bird_monitoring.db`. Make sure the raw data cleaning script has finished running.")
    st.stop()

  engine = create_engine(f"sqlite:///{db_path}")
  df = pd.read_sql("SELECT * FROM bird_observations", con=engine)

  # Cleaning & Type conversions
  df["Date"] = pd.to_datetime(df["Date"])
  df["Observation_Hour"] = (
      df["Start_Time"].astype(str).str.extract(r"(\d{1,2}):")[0].astype(float)
  )

  bool_cols = ["PIF_Watchlist_Status", "Regional_Stewardship_Status", "Flyover_Observed"]
  for col in bool_cols:
    if col in df.columns:
      df[col] = df[col].isin([True, 1, "True", "TRUE"])

  df["Temperature"] = pd.to_numeric(df["Temperature"], errors="coerce")
  df["Humidity"] = pd.to_numeric(df["Humidity"], errors="coerce")
  return df


df = load_survey_data()

# --- Navigation Sidebar ---
with st.sidebar:
  st.markdown("### 🌲 **WildWing Field Hub**")
  st.caption("Avian biodiversity monitoring across National Park habitats.")
  page = st.radio(
      "Jump to:",
      ["Overview", "Field Explorer", "Conservation Notes"],
      label_visibility="collapsed",
  )
  st.divider()

# ==========================================
# 1. OVERVIEW
# ==========================================
if page == "Overview":
  st.title("Avian Biodiversity Field Project")
  st.write(
      "Tracking bird population trends, peak activity hours, and vulnerable "
      "species across our park plots to help rangers and field teams focus conservation efforts."
  )

  # High-level metrics
  m1, m2, m3, m4 = st.columns(4)
  m1.metric("Field Sightings", f"{len(df):,}")
  m2.metric("Species Cataloged", f"{df['Scientific_Name'].nunique():,}")
  m3.metric("Park Units", f"{df['Admin_Unit_Code'].nunique():,}")
  m4.metric("Active Survey Plots", f"{df['Plot_Name'].nunique():,}")

  st.divider()

  col_left, col_right = st.columns([1.1, 0.9], gap="medium")

  with col_left:
    st.subheader("What We're Tracking")
    st.markdown("""
    * **Biodiversity hotspots:** Mapping which forest and grassland plots harbor the highest species richness.
    * **Dawn chorus windows:** Pinpointing the exact morning hours when detectability peaks so field teams don't miss calls.
    * **Watchlist priority:** Monitoring vulnerable species flagged by *Partners in Flight* (PIF) before local populations decline.
    * **Microclimate shifts:** Correlating sudden drop-offs in bird activity with high heat, humidity drops, or trail disturbances.
    """)

  with col_right:
    st.subheader("Habitat Breakdown")
    summary_df = (
        df.groupby("Location_Type")
        .agg(
            Sightings=("Common_Name", "count"),
            Species=("Scientific_Name", "nunique"),
            Plots=("Plot_Name", "nunique"),
        )
        .reset_index()
        .rename(columns={"Location_Type": "Habitat"})
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


# ==========================================
# 2. FIELD EXPLORER (DASHBOARD)
# ==========================================
elif page == "Field Explorer":
  with st.sidebar:
    st.markdown("#### 🎯 Filter Field Data")

    habitats = sorted(df["Location_Type"].dropna().unique().tolist())
    selected_habitats = st.multiselect("Habitats", options=habitats, default=habitats)

    parks = sorted(df["Admin_Unit_Code"].dropna().unique().tolist())
    selected_parks = st.multiselect("Park Units", options=parks, default=parks)

    watchlist_choice = st.radio(
        "Species Status",
        ["All Birds", "Watchlist Only (At-Risk)", "Stable / Secure Only"],
    )

    years = sorted(df["Year"].dropna().unique().tolist())
    selected_years = st.multiselect("Survey Years", options=years, default=years)

  # Filter query
  filtered = df[
      (df["Location_Type"].isin(selected_habitats))
      & (df["Admin_Unit_Code"].isin(selected_parks))
      & (df["Year"].isin(selected_years))
  ]

  if watchlist_choice == "Watchlist Only (At-Risk)":
    filtered = filtered[filtered["PIF_Watchlist_Status"] == True]
  elif watchlist_choice == "Stable / Secure Only":
    filtered = filtered[filtered["PIF_Watchlist_Status"] == False]

  if filtered.empty:
    st.warning("No survey observations match this filter combo. Try widening your habitat or year selection.")
    st.stop()

  # Dynamic counters
  st.subheader("Field Explorer")
  k1, k2, k3, k4 = st.columns(4)
  k1.metric("Sightings in View", f"{len(filtered):,}")
  k2.metric("Species Found", f"{filtered['Scientific_Name'].nunique():,}")
  k3.metric("At-Risk Sightings", f"{(filtered['PIF_Watchlist_Status'] == True).sum():,}")
  k4.metric("Active Plots", f"{filtered['Plot_Name'].nunique():,}")

  tab_species, tab_time, tab_risk, tab_weather, tab_field = st.tabs([
      "Species & Hotspots",
      "Activity Timing",
      "Conservation Focus",
      "Weather & Disturbance",
      "Field Observer Metrics",
  ])

  # --- TAB 1: SPECIES & HOTSPOTS ---
  with tab_species:
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("**Most Frequently Encountered Birds**")
      top_birds = filtered["Common_Name"].value_counts().head(10).reset_index()
      top_birds.columns = ["Species", "Sightings"]
      fig = px.bar(
          top_birds,
          x="Sightings",
          y="Species",
          orientation="h",
          color="Sightings",
          color_continuous_scale="Viridis",
      )
      fig.update_layout(**CHART_THEME, yaxis={"categoryorder": "total ascending"}, showlegend=False)
      st.plotly_chart(fig, use_container_width=True)

    with c2:
      st.markdown("**Plots with the Richest Biodiversity**")
      rich_plots = (
          filtered.groupby(["Plot_Name", "Location_Type"])
          .agg(Species=("Scientific_Name", "nunique"))
          .reset_index()
          .sort_values(by="Species", ascending=False)
          .head(10)
      )
      fig = px.bar(rich_plots, x="Plot_Name", y="Species", color="Location_Type", text="Species")
      fig.update_layout(**CHART_THEME)
      st.plotly_chart(fig, use_container_width=True)

  # --- TAB 2: TIMING ---
  with tab_time:
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("**Seasonal Observation Surges**")
      fig = px.histogram(
          filtered,
          x="Season",
          color="Location_Type",
          barmode="group",
          color_discrete_sequence=["#2b5c8f", "#e07a5f"],
      )
      fig.update_layout(**CHART_THEME)
      st.plotly_chart(fig, use_container_width=True)

    with c2:
      st.markdown("**Diurnal Activity Curve (Hour of Day)**")
      fig = px.histogram(
          filtered.dropna(subset=["Observation_Hour"]),
          x="Observation_Hour",
          color="Location_Type",
          barmode="group",
          nbins=14,
      )
      fig.update_layout(**CHART_THEME, xaxis_title="Hour (24h Clock)")
      st.plotly_chart(fig, use_container_width=True)

  # --- TAB 3: CONSERVATION ---
  with tab_risk:
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("**Most Sighted Watchlist (PIF) Species**")
      watch_df = filtered[filtered["PIF_Watchlist_Status"] == True]
      if not watch_df.empty:
        top_watch = watch_df["Common_Name"].value_counts().head(10).reset_index()
        top_watch.columns = ["Species", "Sightings"]
        fig = px.bar(
            top_watch,
            x="Sightings",
            y="Species",
            orientation="h",
            color="Sightings",
            color_continuous_scale="Reds",
        )
        fig.update_layout(**CHART_THEME, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
      else:
        st.info("No at-risk watchlist species recorded in this filter selection.")

    with c2:
      st.markdown("**Watchlist Ratio by Park Unit**")
      park_watch = filtered.groupby(["Admin_Unit_Code", "PIF_Watchlist_Status"]).size().reset_index(name="Sightings")
      fig = px.bar(park_watch, x="Admin_Unit_Code", y="Sightings", color="PIF_Watchlist_Status", barmode="stack")
      fig.update_layout(**CHART_THEME)
      st.plotly_chart(fig, use_container_width=True)

  # --- TAB 4: WEATHER & DISTURBANCE ---
  with tab_weather:
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("**Survey Conditions: Temperature vs. Humidity**")
      env_df = filtered.dropna(subset=["Temperature", "Humidity"])
      if len(env_df) > 0:
        sample_df = env_df.sample(min(800, len(env_df)))
        fig = px.scatter(
            sample_df,
            x="Temperature",
            y="Humidity",
            color="Location_Type",
            hover_data=["Common_Name", "Admin_Unit_Code"],
            opacity=0.6,
        )
        fig.update_layout(**CHART_THEME)
        st.plotly_chart(fig, use_container_width=True)
      else:
        st.info("No weather logs recorded for this selection.")

    with c2:
      st.markdown("**Human / Site Disturbance Levels**")
      dist_df = filtered.groupby(["Disturbance", "Location_Type"]).size().reset_index(name="Observations")
      fig = px.bar(dist_df, x="Disturbance", y="Observations", color="Location_Type", barmode="group")
      fig.update_layout(**CHART_THEME)
      st.plotly_chart(fig, use_container_width=True)

  # --- TAB 5: OBSERVER METRICS ---
  with tab_field:
    c1, c2 = st.columns(2)
    with c1:
      st.markdown("**Detection Method & Distance Bands**")
      id_dist = filtered.groupby(["ID_Method", "Distance"]).size().reset_index(name="Count")
      fig = px.bar(id_dist, x="ID_Method", y="Count", color="Distance", barmode="stack")
      fig.update_layout(**CHART_THEME)
      st.plotly_chart(fig, use_container_width=True)

    with c2:
      st.markdown("**Flyover vs. Ground/Perch Observations**")
      fly_counts = filtered.groupby("Flyover_Observed").size().reset_index(name="Count")
      fly_counts["Status"] = fly_counts["Flyover_Observed"].map({True: "In Flight", False: "Perched / On Ground"})
      fig = px.pie(fly_counts, names="Status", values="Count", hole=0.45)
      fig.update_layout(**CHART_THEME)
      st.plotly_chart(fig, use_container_width=True)


# ==========================================
# 3. CONSERVATION NOTES
# ==========================================
elif page == "Conservation Notes":
  st.title("Field Findings & Next Steps")
  st.caption("Actionable takeaways synthesized from multi-year point count monitoring.")

  st.markdown("""
  ### 🔍 What the Field Data Shows
  
  * **Forest canopies drive biodiversity:** Multi-layered forest plots host nearly double the bird species of open grasslands due to complex vertical foraging niches.
  * **The 06:00 – 09:00 AM goldmine:** Over **85% of acoustic records** (singing/calling) occur before 9:30 AM. Midday surveys show a steep detection cliff.
  * **Edge habitat vulnerability:** High-risk watchlist species frequently cluster around fragmented borders rather than core forest patches, leaving them vulnerable to shrub encroachment and trail traffic.
  """)

  st.divider()

  col1, col2 = st.columns(2, gap="large")
  with col1:
    st.markdown("#### 🛡️ On-the-Ground Actions")
    st.write(
        "1. **Set Up Micro-Reserves:** Establish strict buffer zones around the top 5 most biodiverse survey plots to limit trail expansion.\n"
        "2. **Restore Grassland Openings:** Clear aggressive woody brush encroaching on primary grassland nesting zones.\n"
        "3. **Pre-Season Bird Call Calibration:** Host calibration walks before spring migrations to ensure consistent distance estimations across volunteer observers."
    )

  with col2:
    st.markdown("#### 📡 Tech & Protocol Upgrades")
    st.write(
        "1. **Deploy Audio Recorders (ARUs):** Install solar-powered acoustic units on key plots to capture the early 05:30–07:00 AM dawn chorus automatically.\n"
        "2. **Log On-Site Microclimates:** Place low-cost temperature/humidity data loggers right at plot centers instead of relying on regional weather stations.\n"
        "3. **Second-Pass Audits:** Schedule follow-up surveys exclusively for plots with historical watchlist species sightings."
    )
