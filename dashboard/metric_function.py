def get_metric_data(df, column_name, agg_func='sum'):
    quarterly_data = (
        df
        .groupby(df['InvoiceDate'].dt.to_period('Q'))[column_name]
        .agg(agg_func)
        .sort_index()
        .tolist()
    )

    # Delta = chênh lệch giữa 2 quý gần nhất
    if len(quarterly_data) > 1:
        delta_val = quarterly_data[-1] - quarterly_data[-2]
    else:
        delta_val = 0

    return quarterly_data, delta_val

def format_million(value, suffix=""):
    return f"{value/1_000_000:.2f}M{suffix}"