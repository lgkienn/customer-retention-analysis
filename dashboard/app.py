# ======================================================
# IMPORT LIBRARIES & PROJECT MODULES
# ======================================================
# Streamlit: UI dashboard
# Pandas: data manipulation
# Plotly: interactive charts
import streamlit as st
import pandas as pd
import plotly.express as px

# Custom project modules
from clean_data import read_clean_export_data
from rfm_segment import build_rfm_segment
from metric_function import get_metric_data, format_million
from plot_distribution import plot_rfm_distribution
from heatmap_plot import plot_rf_heatmap_imshow
from segment_movement_plot import build_segment_movement_df, plot_segment_movement
from snapshot_plot import (
    generate_rfm_snapshots,
    plot_segment_sankey,
    build_migration_between_snapshots,
    generate_rfm_snapshots_cached
)
from cohort import (
    build_cohort_df,
    build_retention_table,
    plot_cohort_heatmap,
    add_segment_to_cohort
)
from cohort_revenue import (
    build_revenue_cohort_table,
    plot_revenue_cohort_heatmap
)


# ======================================================
# I. LOAD, CLEAN & PREPARE BASE DATA
# ======================================================
# Read raw ecommerce data and apply cleaning logic
csv_path = "data/ecommerce_retail.csv"  # full dataset
df_customers = read_clean_export_data(csv_path)

# Build RFM score & segment for each customer
df_segment = build_rfm_segment(df_customers)

# Create lightweight mapping table: Customer → Segment
segment_map = df_segment[["CustomerID", "Segment"]]

# Merge segment info back into transaction-level table
df_txn = df_customers.merge(
    segment_map,
    on="CustomerID",
    how="left"
)

# Keep Segment column explicit (guest customers remain NaN)
df_txn["Segment"] = df_txn["Segment"]


# ======================================================
# II. OVERALL KPI CALCULATIONS
# ======================================================
# Core business metrics
total_transaction = len(df_customers)
total_revenue = df_customers["Revenue"].sum()
total_quantity = df_customers["Quantity"].sum()

# Percentage of registered customers
customer_counts = df_customers["CustomerType"].value_counts()
reg_count = customer_counts.get("Registered", 0)
total_customers = customer_counts.sum()
percent_registered = (reg_count / total_customers) * 100


# ======================================================
# III. TIME-SERIES DATA FOR KPI SPARKLINES
# ======================================================
# Revenue trend
revenue_series, revenue_delta = get_metric_data(
    df_customers, "Revenue", "sum"
)

# Quantity trend
qty_series, qty_delta = get_metric_data(
    df_customers, "Quantity", "sum"
)

# Transaction count trend
trans_series, trans_delta = get_metric_data(
    df_customers, "InvoiceNo", "nunique"
)

# Registered customer % by quarter
quarterly_reg = (
    df_customers
    .groupby(df_customers["InvoiceDate"].dt.to_period("Q"))
    .apply(lambda x: (x["CustomerType"] == "Registered").sum() / len(x) * 100)
    .sort_index()
    .tolist()
)

# Change vs previous quarter
reg_delta = (
    quarterly_reg[-1] - quarterly_reg[-2]
    if len(quarterly_reg) > 1 else 0
)


# ======================================================
# IV. DASHBOARD HEADER & KPI DISPLAY
# ======================================================
st.title("E-commerce Dashboard")
st.caption("Sparkline shows quarterly trend (Year–Quarter)")

row = st.columns(4)

# KPI 1: Transactions
with row[0]:
    st.metric(
        label="Total Transactions (M)",
        value=format_million(len(df_customers)),
        delta=format_million(trans_delta),
        chart_data=trans_series,
        chart_type="area",
        border=True
    )

# KPI 2: Revenue
with row[1]:
    st.metric(
        label="Total Revenue ($M)",
        value=format_million(total_revenue),
        delta=format_million(revenue_delta),
        chart_data=revenue_series,
        chart_type="area",
        border=True
    )

# KPI 3: Quantity
with row[2]:
    st.metric(
        label="Total Quantity (M)",
        value=format_million(total_quantity),
        delta=format_million(qty_delta),
        chart_data=qty_series,
        chart_type="area",
        border=True
    )

# KPI 4: Registered customer %
with row[3]:
    st.metric(
        label="% Registered",
        value=f"{percent_registered:.1f}%",
        delta=f"{reg_delta:.1f}%",
        chart_data=quarterly_reg,
        chart_type="area",
        border=True
    )


# ======================================================
# V. SEGMENT DISTRIBUTION & CONTRIBUTION
# ======================================================
# Define segment order and color palette
segment_order = [
    "Champions", "Loyal", "Potential Loyalist", "New Customers",
    "Promising", "Need Attention", "About To Sleep", "At Risk",
    "Cannot Lose Them", "Hibernating customers", "Lost customers"
]

segment_color_map = {
    "Champions": "#1f77b4",
    "Loyal": "#2ca02c",
    "Potential Loyalist": "#98df8a",
    "New Customers": "#ffbb78",
    "Promising": "#ff7f0e",
    "Need Attention": "#d62728",
    "About To Sleep": "#9467bd",
    "At Risk": "#8c564b",
    "Cannot Lose Them": "#e377c2",
    "Hibernating customers": "#7f7f7f",
    "Lost customers": "#bcbd22"
}

col1, col2 = st.columns(2)

# ------------------------------------------------------
# Customer count by segment
# ------------------------------------------------------
segment_count = (
    df_segment
    .groupby("Segment")["CustomerID"]
    .nunique()
    .reset_index(name="CustomerCount")
    .sort_values("CustomerCount", ascending=False)
)

fig_count = px.bar(
    segment_count,
    x="CustomerCount",
    y="Segment",
    text="CustomerCount",
    orientation="h",
    title="Number of Customers by RFM Segment",
    color="Segment",
    color_discrete_map=segment_color_map
)

# Emphasize key segments
fig_count.update_traces(
    marker_line_width=[
        3 if s in ["Champions", "At Risk"] else 0
        for s in segment_count["Segment"]
    ],
    marker_line_color="black",
    textposition="outside"
)

fig_count.update_layout(
    xaxis_title="Number of Customers",
    yaxis_title="RFM Segment",
    xaxis=dict(rangemode="tozero"),
    showlegend=False
)

with col1:
    st.plotly_chart(fig_count, use_container_width=True)


# ------------------------------------------------------
# Revenue contribution by segment
# ------------------------------------------------------
segment_revenue = (
    df_segment
    .groupby("Segment")["Revenue"]
    .sum()
    .reset_index(name="Revenue")
)

segment_revenue["RevenuePct"] = (
    segment_revenue["Revenue"]
    / segment_revenue["Revenue"].sum() * 100
)

segment_revenue = segment_revenue.sort_values(
    "RevenuePct", ascending=False
)

# Group small segments into "Others"
revenue_cutoff = 5
segment_revenue["SegmentGrouped"] = segment_revenue.apply(
    lambda x: x["Segment"] if x["RevenuePct"] >= revenue_cutoff else "Others",
    axis=1
)

segment_revenue_grouped = (
    segment_revenue
    .groupby("SegmentGrouped", as_index=False)
    .agg({"RevenuePct": "sum"})
    .sort_values("RevenuePct", ascending=False)
)

fig_revenue_grouped = px.bar(
    segment_revenue_grouped,
    x="RevenuePct",
    y="SegmentGrouped",
    text=segment_revenue_grouped["RevenuePct"].round(1).astype(str) + "%",
    orientation="h",
    title="Revenue Contribution by Segment (Grouped)",
    color="SegmentGrouped",
    color_discrete_map={**segment_color_map, "Others": "#cccccc"}
)

fig_revenue_grouped.update_traces(textposition="outside")
fig_revenue_grouped.update_layout(
    xaxis_title="Revenue Contribution (%)",
    yaxis_title="Segment",
    xaxis=dict(range=[0, 70], dtick=10),
    showlegend=False
)

with col2:
    st.plotly_chart(fig_revenue_grouped, use_container_width=True)


# ======================================================
# VI. RFM SCORE DISTRIBUTION
# ======================================================
st.subheader("RFM Distribution Analysis")

rfm_dim = st.selectbox(
    "Select RFM Dimension",
    options=["R", "F", "M"],
    format_func=lambda x: {
        "R": "Recency",
        "F": "Frequency",
        "M": "Monetary"
    }[x]
)

fig_distribution = plot_rfm_distribution(
    df=df_segment,
    dim=rfm_dim,
    segment_order=segment_order,
    segment_color_map=segment_color_map
)

st.plotly_chart(fig_distribution, use_container_width=True)


# ======================================================
# VII. RF HEATMAP ANALYSIS
# ======================================================
# Map numeric R/F scores to readable labels
r_mapping = {
    5: "Recent", 4: "Active", 3: "Warm",
    2: "Cold", 1: "Hibernating"
}

f_mapping = {
    4: "Loyal", 3: "Regular",
    2: "Occasional", 1: "One-time"
}

recency_order = ["Recent", "Active", "Warm", "Cold", "Hibernating"]
frequency_order = ["Loyal", "Regular", "Occasional", "One-time"]

df_segment["R_Name"] = df_segment["R_Score"].map(r_mapping)
df_segment["F_Name"] = df_segment["F_Score"].map(f_mapping)

# Ensure heatmap axes follow business order
df_segment["R_Name"] = pd.Categorical(
    df_segment["R_Name"],
    categories=recency_order,
    ordered=True
)

df_segment["F_Name"] = pd.Categorical(
    df_segment["F_Name"],
    categories=frequency_order,
    ordered=True
)

st.subheader("Heatmap Analysis")

value_option = st.selectbox(
    "Select Value Dimension",
    options=["CustomerCount", "Revenue"],
    format_func=lambda x: {
        "CustomerCount": "Number of Customers",
        "Revenue": "Revenue"
    }[x]
)

fig_heatmap = plot_rf_heatmap_imshow(
    df=df_segment,
    value_type=value_option
)

st.plotly_chart(fig_heatmap, use_container_width=True)


# ======================================================
# VIII. SEGMENT MOVEMENT OVER TIME
# ======================================================
st.subheader("Segment Movement over Time")

time_level = st.selectbox(
    "Time granularity",
    ["Day", "Month", "Quarter", "Year"],
    index=2
)

movement_df = build_segment_movement_df(
    df_txn=df_txn,
    time_level=time_level
)

fig = plot_segment_movement(movement_df, time_level)
st.plotly_chart(fig, use_container_width=True)


# ======================================================
# IX. CUSTOMER SEGMENT MIGRATION (SANKEY)
# ======================================================
st.subheader("Customer Segment Migration")

TIME_FREQ_MAP = {
    "Day": "D",
    "Month": "M",
    "Quarter": "Q",
    "Year": "Y"
}

time_level = st.selectbox(
    "Snapshot Granularity",
    ["Month", "Quarter", "Year"],
    index=1
)

freq = TIME_FREQ_MAP[time_level]

snapshot_df = generate_rfm_snapshots(
    df_txn=df_txn,
    freq=freq
)

available_periods = sorted(snapshot_df["Period"].unique())

col1, col2 = st.columns(2)

with col1:
    period_past = st.selectbox(
        "Past Snapshot",
        available_periods,
        index=max(0, len(available_periods) - 2)
    )

with col2:
    period_now = st.selectbox(
        "Current Snapshot",
        available_periods,
        index=len(available_periods) - 1
    )

migration_df = build_migration_between_snapshots(
    snapshot_df,
    past_period=period_past,
    now_period=period_now
)

fig = plot_segment_sankey(
    migration_df,
    segment_color_map
)

st.plotly_chart(fig, use_container_width=True)


# ======================================================
# X. COHORT ANALYSIS
# ======================================================
snapshot_df = generate_rfm_snapshots_cached(
    df_txn=df_txn,
    freq=freq
)

# Build cohort base table once
cohort_df = build_cohort_df(df_txn)
cohort_segment_df = add_segment_to_cohort(
    cohort_df, snapshot_df
)

st.subheader("Cohort Analysis")

segment_option = st.selectbox(
    "Select Segment",
    options=["All"] + segment_order,
    key="cohort_segment_select"
)

# Apply segment filter if needed
if segment_option == "All":
    cohort_filtered = cohort_df
else:
    cohort_filtered = cohort_segment_df[
        cohort_segment_df["Segment"] == segment_option
    ]

# ------------------------------------------------------
# Customer retention cohort
# ------------------------------------------------------
customer_retention = build_retention_table(cohort_filtered)

if customer_retention.empty:
    st.warning(
        "Not enough data to build **Customer Retention Cohort** for this segment."
    )
else:
    fig_customer = plot_cohort_heatmap(customer_retention)
    st.plotly_chart(
        fig_customer,
        use_container_width=True,
        key="cohort_customer_segment_chart"
    )

# ------------------------------------------------------
# Revenue retention cohort
# ------------------------------------------------------
revenue_retention = build_revenue_cohort_table(cohort_filtered)

if revenue_retention.empty:
    st.warning(
        "Not enough data to build **Revenue Retention Cohort** for this segment."
    )
else:
    fig_revenue = plot_revenue_cohort_heatmap(revenue_retention)
    st.plotly_chart(
        fig_revenue,
        use_container_width=True,
        key="cohort_revenue_segment_chart"
    )
