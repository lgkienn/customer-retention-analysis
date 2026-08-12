import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def classify_rfm_segment(row):
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 3:
        return "Loyal"
    elif r >= 4 and f <= 2:
        return "New Customers"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f <= 2:
        return "Hibernating customers"
    else:
        return "Need Attention"

def build_rfm_snapshot(
    df_txn: pd.DataFrame,
    snapshot_date: pd.Timestamp
):
    df = df_txn[df_txn["InvoiceDate"] <= snapshot_date].copy()

    rfm = (
        df.groupby("CustomerID")
        .agg(
            Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Revenue", "sum")
        )
        .reset_index()
    )

    # ========= Score RFM =========
    rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1,2,3,4,5]).astype(int)

    # ========= Classify Segment =========
    rfm["Segment"] = rfm.apply(classify_rfm_segment, axis=1)

    rfm["SnapshotDate"] = snapshot_date

    return rfm[["CustomerID", "SnapshotDate", "Segment"]]

def generate_rfm_snapshots(df_txn: pd.DataFrame, freq: str = "M"):
    # Chắc chắn InvoiceDate là datetime
    df_txn["InvoiceDate"] = pd.to_datetime(df_txn["InvoiceDate"], errors="coerce")
    
    # Tạo các period
    snapshot_periods = (
        df_txn["InvoiceDate"]
        .dt.to_period(freq)
        .sort_values()
        .unique()
    )

    snapshots = []

    for period in snapshot_periods:
        snap_date = period.to_timestamp(how="end")
        snap_df = build_rfm_snapshot(df_txn, snap_date)
        snap_df["Period"] = str(period)
        snapshots.append(snap_df)

    return pd.concat(snapshots, ignore_index=True)

def build_segment_migration_df(snapshot_df: pd.DataFrame):

    snapshot_df = snapshot_df.sort_values(["CustomerID", "SnapshotDate"])

    snapshot_df["PrevSegment"] = (
        snapshot_df
        .groupby("CustomerID")["Segment"]
        .shift(1)
    )

    migration_df = snapshot_df.dropna(subset=["PrevSegment"])

    return migration_df

def plot_segment_sankey(migration_df, segment_color_map):

    links = (
        migration_df
        .groupby(["PrevSegment", "Segment"])
        .size()
        .reset_index(name="Count")
    )

    links = links[links["Count"] > 5]

    # Labels
    source_labels = [f"{s} (Past)" for s in links["PrevSegment"].unique()]
    target_labels = [f"{s} (Now)" for s in links["Segment"].unique()]
    all_labels = source_labels + target_labels

    label_idx = {label: i for i, label in enumerate(all_labels)}

    source = links["PrevSegment"].apply(lambda x: label_idx[f"{x} (Past)"])
    target = links["Segment"].apply(lambda x: label_idx[f"{x} (Now)"])
    value = links["Count"]

    # =======================
    # LINK COLOR = PrevSegment
    # =======================
    def rgba(hex_color, alpha=0.4):
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r},{g},{b},{alpha})"

    link_colors = links["PrevSegment"].map(
        lambda s: rgba(segment_color_map.get(s, "#BDBDBD"))
    )

    # =======================
    # NODE COLORS
    # =======================
    node_colors = [
        segment_color_map.get(label.replace(" (Past)", "").replace(" (Now)", ""), "#BDBDBD")
        for label in all_labels
    ]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=30,
            thickness=30,
            line=dict(color="black", width=0.5),
            label=all_labels,
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors
        )
    ))

    fig.update_layout(
        title_text="<b>Customer Segment Migration Analysis</b>",
        font_size=14,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    return fig

def build_migration_between_snapshots(snapshot_df, past_period, now_period):

    df_past = snapshot_df[snapshot_df["Period"] == past_period]
    df_now = snapshot_df[snapshot_df["Period"] == now_period]

    migration_df = (
        df_past[["CustomerID", "Segment"]]
        .merge(
            df_now[["CustomerID", "Segment"]],
            on="CustomerID",
            how="inner",
            suffixes=("Prev", "Now")
        )
    )

    migration_df = migration_df.rename(
        columns={
            "SegmentPrev": "PrevSegment",
            "SegmentNow": "Segment"
        }
    )

    return migration_df

@st.cache_data(show_spinner="Building RFM snapshots...")
def generate_rfm_snapshots_cached(df_txn, freq):
    return generate_rfm_snapshots(df_txn, freq)
