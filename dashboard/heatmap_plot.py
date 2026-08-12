import pandas as pd
import plotly.express as px

recency_order = ["Recent", "Active", "Warm", "Cold", "Hibernating"]
frequency_order = ["Loyal", "Regular", "Occasional", "One-time"]

def plot_rf_heatmap_imshow(
    df: pd.DataFrame,
    value_type: str = "CustomerCount"  # or "Revenue"
):
    df = df.copy()

    # =======================
    # Aggregate
    # =======================
    if value_type == "CustomerCount":
        pivot_df = (
            df.groupby(["F_Name", "R_Name"])["CustomerID"]
              .nunique()
              .unstack(fill_value=0)
        )
        colorbar_title = "Number of Customers"

    else:
        pivot_df = (
            df.groupby(["F_Name", "R_Name"])["Revenue"]
              .sum()
              .unstack(fill_value=0)
        )
        colorbar_title = "Total Revenue"

    # Ensure correct order
    pivot_df = pivot_df.reindex(
        index=frequency_order,
        columns=recency_order,
        fill_value=0
    )

    # =======================
    # Plot heatmap
    # =======================
    fig = px.imshow(
        pivot_df,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale="Blues"
    )

    fig.update_layout(
        title=f"R × F Heatmap ({colorbar_title})",
        xaxis_title="Recency",
        yaxis_title="Frequency",
        coloraxis_colorbar=dict(title=colorbar_title)
    )

    return fig
