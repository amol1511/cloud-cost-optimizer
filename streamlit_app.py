import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from src.rules import Thresholds
from src.loaders import load_dataset
from src.analyzer import detect_compute_recommendations, detect_storage_recommendations, summarize_costs

st.set_page_config(page_title="Cloud Cost Optimization Tool", layout="wide")

st.title("💸 Cloud Cost Optimization Tool")
st.write("Analyze cloud cost CSVs (AWS/Azure/GCP) and generate savings recommendations.")

with st.sidebar:
    st.header("Settings")
    idle_cpu = st.slider("Idle CPU threshold (%)", 0, 20, 5, 1)
    under_cpu = st.slider("Underutilized CPU threshold (%)", 5, 50, 20, 1)
    min_hours = st.slider("Min active hours/month", 0, 720, 100, 10)
    min_cost = st.slider("Min monthly cost (USD)", 0, 200, 5, 1)
    rightsize_save = st.slider("Rightsizing savings (%)", 0, 80, 35, 5) / 100.0
    idle_save = st.slider("Idle stop savings (%)", 0, 100, 90, 5) / 100.0
    storage_cold_days = st.slider("Cold storage if last access > days", 0, 365, 30, 5)
    storage_save = st.slider("Storage tiering savings (%)", 0, 100, 40, 5) / 100.0
    st.markdown("---")
    sample = st.checkbox("Use sample dataset", value=True)

uploaded = st.file_uploader("Upload CSV", type=["csv"], accept_multiple_files=False)

if sample and uploaded is None:
    path = "sample_data.csv"
    st.caption("Using included sample_data.csv")
else:
    if uploaded is None:
        st.info("Upload a CSV or tick 'Use sample dataset'.")
        st.stop()
    path = uploaded

df = load_dataset(path)
th = Thresholds(
    idle_cpu_pct=idle_cpu,
    underutil_cpu_pct=under_cpu,
    min_hours_active=min_hours,
    min_cost_consider=min_cost,
    rightsizing_savings_pct=rightsize_save,
    idle_stop_savings_pct=idle_save,
    storage_cold_days=storage_cold_days,
    storage_savings_pct=storage_save,
)

# Summary
summary = summarize_costs(df)
col1, col2, col3 = st.columns(3)
col1.metric("Total Monthly Cost (USD)", f"{summary['total_cost']:,.2f}")
col2.metric("Services", str(summary['by_service']['service'].nunique()))
col3.metric("Resources (rows)", f"{len(df):,}")

st.markdown("## Cost by Service")
fig1, ax1 = plt.subplots()
ax1.bar(summary['by_service']['service'], summary['by_service']['cost_usd_total'])
ax1.set_xlabel("Service")
ax1.set_ylabel("Cost (USD)")
ax1.set_title("Cost by Service")
plt.xticks(rotation=45, ha='right')
st.pyplot(fig1)

if summary['by_env'] is not None and not summary['by_env'].empty:
    st.markdown("## Cost by Env Tag")
    fig2, ax2 = plt.subplots()
    ax2.bar(summary['by_env']['env'], summary['by_env']['cost_usd_total'])
    ax2.set_xlabel("env")
    ax2.set_ylabel("Cost (USD)")
    ax2.set_title("Cost by env tag")
    st.pyplot(fig2)

st.markdown("## Top Costly Resources")
st.dataframe(summary['top_resources'][['provider','service','resource_id','region','month','cost_usd','cpu_avg','hours_running','tags']])

# Recommendations
st.markdown("## Recommendations")
compute_recs = detect_compute_recommendations(df, th)
storage_recs = detect_storage_recommendations(df, th)

tab1, tab2, tab3 = st.tabs(["Compute", "Storage", "All"])

with tab1:
    st.subheader("Compute Recommendations")
    st.dataframe(compute_recs)

with tab2:
    st.subheader("Storage Recommendations")
    st.dataframe(storage_recs)

with tab3:
    st.subheader("All Recommendations")
    all_recs = pd.concat([compute_recs, storage_recs], ignore_index=True)
    if all_recs.empty:
        st.info("No recommendations found with current thresholds.")
    else:
        st.dataframe(all_recs)
        total_savings = all_recs['estimated_monthly_savings_usd'].sum()
        st.metric("Estimated Monthly Savings (USD)", f"{total_savings:,.2f}")
        csv = all_recs.to_csv(index=False).encode('utf-8')
        st.download_button("Download Recommendations CSV", csv, "recommendations.csv", "text/csv")


st.markdown("---")
st.caption("Heuristic-based advisor. Validate before changes in production.")
