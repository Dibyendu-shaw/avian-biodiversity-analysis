# 🦅 Avian Biodiversity & Conservation Analytics Platform

An automated data pipeline, exploratory intelligence engine, and interactive decision-support dashboard for multi-habitat avian population monitoring across Forest and Grassland ecosystems.

---

## 📌 Project Overview
Ecological monitoring data across 11 National Park administrative units was consolidated, standardized, and structured into a relational SQLite database. The platform analyzes species richness, temporal and diurnal activity patterns, environmental drivers, observer variations, and Partners in Flight (PIF) conservation priority levels.

---

## 🛠️ Architecture & Tech Stack
* **Language & Runtime**: Python 3.12+
* **Data Processing & Database**: `pandas`, `SQLAlchemy`, `SQLite3`, `openpyxl`
* **Interactive Visualization**: `Plotly Express`, `Plotly Graph Objects`
* **Web Dashboard**: `Streamlit`
* **Version Control & Structure**: Modular project repository

---

## 📂 Repository Structure
```text
BIRD_OBSERVATION_ANALYSIS/
├── dashboard/
│   └── app.py                        # Multi-page Streamlit Analytics Application
├── data/
│   ├── Bird_Monitoring_Data_FOREST.XLSX
│   ├── Bird_Monitoring_Data_GRASSLAND.XLSX
│   ├── bird_monitoring.db            # Structured SQLite Database
│   └── cleaned_bird_observations.csv # Processed Master Dataset
├── notebooks/
│   ├── 01_data_cleaning.ipynb        # Automated Ingestion & Cleaning Pipeline
│   └── 02_eda_analysis.ipynb         # Statistical EDA & Visualization Suite
├── sql/
│   └── queries.sql                   # Production SQL Analytical Queries
└── README.md
