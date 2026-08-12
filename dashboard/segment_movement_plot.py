import pandas as pd
import plotly.express as px

### Distribution charts:
segment_order = [
    "Champions",
    "Loyal",
    "Potential Loyalist",
    "New Customers",
    "Promising",
    "Need Attention",
    "About To Sleep",
    "At Risk",
    "Cannot Lose Them",
    "Hibernating customers",
    "Lost customers"
]

segment_color_map = {
    "Champions": "#1f77b4",          # xanh đậm – best customers
    "Loyal": "#2ca02c",              # xanh lá
    "Potential Loyalist": "#98df8a", # xanh nhạt
    "New Customers": "#ffbb78",      # cam nhạt
    "Promising": "#ff7f0e",          # cam
    "Need Attention": "#d62728",     # đỏ nhạt
    "About To Sleep": "#9467bd",     # tím
    "At Risk": "#8c564b",            # nâu
    "Cannot Lose Them": "#e377c2",   # hồng
    "Hibernating customers": "#7f7f7f", # xám
    "Lost customers": "#bcbd22"      # vàng xám
}

def add_time_period(df: pd.DataFrame, time_level: str):
    df = df.copy()

    if time_level == "Day":
        df["Period"] = df["InvoiceDate"].dt.date

    elif time_level == "Month":
        df["Period"] = df["InvoiceDate"].dt.to_period("M").astype(str)

    elif time_level == "Quarter":
        df["Period"] = df["InvoiceDate"].dt.to_period("Q").astype(str)

    elif time_level == "Year":
        df["Period"] = df["InvoiceDate"].dt.year.astype(str)

    return df

def build_segment_movement_df(
    df_txn: pd.DataFrame,
    time_level: str
):
    df_time = add_time_period(df_txn, time_level)

    movement_df = (
        df_time
        .groupby(["Period", "Segment"])["CustomerID"]
        .nunique()
        .reset_index(name="Customers")
    )

    return movement_df

import plotly.express as px

def plot_segment_movement(movement_df, time_level):

    fig = px.line(
        movement_df,
        x="Period",
        y="Customers",
        color="Segment",
        category_orders={"Segment": ["Guest"] + segment_order},
        color_discrete_map={
            **segment_color_map,
            "Guest": "#BDBDBD"
        }
    )

    fig.update_traces(
        line=dict(
            width=2,          # mỏng hơn (1.5–2 là đẹp)
            shape="spline"    # làm đường cong mềm
        ),
        opacity=0.85          # giảm gắt màu
    )

    fig.update_layout(
        title=f"Segment Contribution over Time ({time_level})",
        xaxis_title="Time",
        yaxis_title="Active Customers",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig
