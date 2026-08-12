import pandas as pd
import plotly.express as px

def build_revenue_cohort_table(cohort_df: pd.DataFrame):

    revenue_table = (
        cohort_df
        .groupby(["CohortMonth", "CohortIndex"])["Revenue"]
        .sum()
        .reset_index()
    )

    if revenue_table.empty:
        return pd.DataFrame()

    revenue_pivot = revenue_table.pivot(
        index="CohortMonth",
        columns="CohortIndex",
        values="Revenue"
    )

    if revenue_pivot.shape[1] == 0:
        return pd.DataFrame()

    first_col = revenue_pivot.columns.min()

    revenue_retention = revenue_pivot.divide(
        revenue_pivot[first_col],
        axis=0
    ).round(3)

    revenue_retention.index = revenue_retention.index.astype(str)

    return revenue_retention


def plot_revenue_cohort_heatmap(revenue_retention):

    fig = px.imshow(
        revenue_retention,
        text_auto=".0%",
        aspect="auto",
        color_continuous_scale="Greens"
    )

    fig.update_layout(
        title="Revenue Retention Cohort Analysis",
        xaxis_title="Months Since First Purchase",
        yaxis_title="Cohort (First Purchase Month)",
        coloraxis_colorbar=dict(title="Revenue Retention"),
        margin=dict(l=60, r=40, t=60, b=40)
    )

    return fig
