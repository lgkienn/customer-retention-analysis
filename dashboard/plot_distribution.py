import pandas as pd
import plotly.express as px

# =======================
# RFM DEFINITIONS
# =======================

RFM_CONFIG = {
    "R": {
        "score_col": "R_Score",
        "label_col": "R_Name",
        "mapping": {
            5: "Recent",
            4: "Active",
            3: "Warm",
            2: "Cold",
            1: "Hibernating"
        },
        "order": ["Recent", "Active", "Warm", "Cold", "Hibernating"],
        "axis_title": "Recency Status"
    },
    "F": {
        "score_col": "F_Score",
        "label_col": "F_Name",
        "mapping": {
            4: "Loyal",
            3: "Regular",
            2: "Occasional",
            1: "One-time"
        },
        "order": ["Loyal", "Regular", "Occasional", "One-time"],
        "axis_title": "Frequency Status"
    },
    "M": {
        "score_col": "M_Score",
        "label_col": "M_Name",
        "mapping": {
            5: "Whales",
            4: "High Spenders",
            3: "Mid-range",
            2: "Low Spenders",
            1: "Entry Level"
        },
        "order": ["Whales", "High Spenders", "Mid-range", "Low Spenders", "Entry Level"],
        "axis_title": "Monetary Status"
    }
}

def plot_rfm_distribution(
    df: pd.DataFrame,
    dim: str,
    segment_order: list,
    segment_color_map: dict
):
    """
    dim: 'R', 'F', hoặc 'M'
    """

    cfg = RFM_CONFIG[dim]

    # Map score → label
    df = df.copy()
    df[cfg["label_col"]] = df[cfg["score_col"]].map(cfg["mapping"])

    # Convert to categorical để giữ thứ tự
    df[cfg["label_col"]] = pd.Categorical(
        df[cfg["label_col"]],
        categories=cfg["order"],
        ordered=True
    )

    # Aggregate
    count_table = (
        df
        .groupby([cfg["label_col"], "Segment"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=cfg["order"], columns=segment_order, fill_value=0)
    )

    # Long format cho Plotly
    df_plot = (
        count_table
        .reset_index()
        .melt(
            id_vars=cfg["label_col"],
            var_name="Segment",
            value_name="CustomerCount"
        )
    )

    # Plot
    fig = px.bar(
        df_plot,
        x=cfg["label_col"],
        y="CustomerCount",
        color="Segment",
        barmode="group",
        color_discrete_map=segment_color_map,
        category_orders={
            cfg["label_col"]: cfg["order"],
            "Segment": segment_order
        }
    )

    fig.update_layout(
        title=f"Distribution of {dim} by RFM Segment",
        xaxis_title=cfg["axis_title"],
        yaxis_title="Number of Customers",
        legend_title="RFM Segment",
        yaxis=dict(rangemode="tozero"),
        margin=dict(l=20, r=20, t=60, b=20),
        bargap=0.001,        # Giảm khoảng cách giữa các nhóm
        # bargroupgap=0.0 # Giảm khoảng cách giữa các cột thành phần
        # barmode='group'    # Đảm bảo các cột nằm cạnh nhau
    )
    # Chỉnh tất cả các cột béo lên
    fig.update_traces(width=0.2)

    return fig
