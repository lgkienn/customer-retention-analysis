import pandas as pd
import plotly.express as px

def build_cohort_df(df_txn: pd.DataFrame):

    df = df_txn.copy()

    # Ensure datetime
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # Tháng giao dịch
    df["OrderMonth"] = df["InvoiceDate"].dt.to_period("M")

    # Tháng first purchase (cohort)
    df["CohortMonth"] = (
        df.groupby("CustomerID")["OrderMonth"]
          .transform("min")
    )

    # Cohort index (số tháng kể từ lần mua đầu)
    df["CohortIndex"] = (
        (df["OrderMonth"].dt.year - df["CohortMonth"].dt.year) * 12 +
        (df["OrderMonth"].dt.month - df["CohortMonth"].dt.month) + 1
    )

    return df

def build_retention_table(cohort_df: pd.DataFrame):

    cohort_counts = (
        cohort_df
        .groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
        .nunique()
        .reset_index()
    )

    if cohort_counts.empty:
        return pd.DataFrame()

    cohort_pivot = cohort_counts.pivot(
        index="CohortMonth",
        columns="CohortIndex",
        values="CustomerID"
    )

    # 🚨 Defensive check
    if cohort_pivot.shape[1] == 0:
        return pd.DataFrame()

    # Nếu không có CohortIndex = 1 → không thể tính retention
    first_col = cohort_pivot.columns.min()

    cohort_retention = cohort_pivot.divide(
        cohort_pivot[first_col],
        axis=0
    ).round(3)

    cohort_retention.index = cohort_retention.index.astype(str)

    return cohort_retention




def plot_cohort_heatmap(cohort_retention):

    fig = px.imshow(
        cohort_retention,
        text_auto=".0%",
        aspect="auto",
        color_continuous_scale="Blues"
    )

    fig.update_layout(
        title="Customer Retention Cohort Analysis",
        xaxis_title="Months Since First Purchase",
        yaxis_title="Cohort (First Purchase Month)",
        coloraxis_colorbar=dict(title="Retention Rate"),
        margin=dict(l=60, r=40, t=60, b=40)
    )

    return fig

def add_segment_to_cohort(cohort_df, snapshot_df):
    """
    Gắn Segment (snapshot mới nhất) vào cohort_df
    """

    latest_period = snapshot_df["Period"].max()

    segment_map = (
        snapshot_df[snapshot_df["Period"] == latest_period]
        [["CustomerID", "Segment"]]
        .rename(columns={"Segment": "CurrentSegment"})
    )

    cohort_segment_df = cohort_df.merge(
        segment_map,
        on="CustomerID",
        how="left"
    )

    # Đổi tên về Segment cho thống nhất downstream
    cohort_segment_df["Segment"] = (
        cohort_segment_df["CurrentSegment"]
        .fillna("Guest")
    )

    cohort_segment_df = cohort_segment_df.drop(columns=["CurrentSegment"])

    return cohort_segment_df


def build_segment_cohort_retention(cohort_segment_df, segment_name):

    df = cohort_segment_df[
        cohort_segment_df["Segment"] == segment_name
    ]

    cohort_counts = (
        df
        .groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
        .nunique()
        .reset_index()
        .pivot(
            index="CohortMonth",
            columns="CohortIndex",
            values="CustomerID"
        )
    )

    retention = cohort_counts.divide(
        cohort_counts.iloc[:, 0],
        axis=0
    ).round(3)

    retention.index = retention.index.astype(str)

    return retention

