## Practice re-code clean_data
import pandas as pd

def read_clean_export_data(csv_path:str) -> pd.DataFrame:

    usecols = [
        "InvoiceNo", "StockCode", "Description",
        "Quantity", "InvoiceDate",
        "UnitPrice", "CustomerID","Country"
    ]

    df = pd.read_csv(csv_path, usecols= usecols, dtype = {"InvoiceNo":str,"StockCode":str},
                     parse_dates=["InvoiceDate"])
    
    #Remove cancelled transaction

    df = df[~df["InvoiceNo"].str.startswith("C")]

    #Valid Invoice

    df["ValidStockCode"] = df["StockCode"].str.match(r"^\d{5}.*$")

    #CustomerType
    df["CustomerType"] = df["CustomerID"].isna().map(
            {True: "Guest",
             False:"Registered"}
    )

    #Fill description
    desc_map = df.loc[df["Description"].notna(),["StockCode","Description"]]\
        .drop_duplicates("StockCode").\
            set_index("StockCode")["Description"]
    
    df["Description"] = df["Description"].fillna(df["StockCode"].map(desc_map))\
        .fillna("Unknown")
    
    #fill price
    price_map = df.loc[df["UnitPrice"]>0,["StockCode","UnitPrice"]]\
        .drop_duplicates('StockCode').set_index("StockCode")["UnitPrice"]
    
    zero_price_mask = (df["UnitPrice"]==0)

    df.loc[zero_price_mask,'UnitPrice'] = df.loc[zero_price_mask,"StockCode"].map(price_map)

    df = df[(df["ValidStockCode"])]

    df["Revenue"] = df["Quantity"]*df['UnitPrice']

    return df

# ###
# def build_rfm_segment(
#         df,
#         analysis_date = "2011-12-31"
# ):
#     """Build RFM table and classify customer segments."""

#     analysis_date = pd.to_datetime(analysis_date)

#     #1. Build RFM base
#     rfm = (df.groupby("CustomerID")
#         .agg({
#             "InvoiceDate":"max",
#             "InvoiceNo":"nunique",
#             "Revenue":"sum"
#         }).reset_index())
    
#     #2. Calculate R,F,M
#     rfm['Recency'] = (analysis_date - rfm["InvoiceDate"]).dt.days
#     rfm['Frequency'] = rfm['InvoiceNo']
#     rfm['Monetary'] = rfm['Revenue']

#     rfm["R_Score"] = pd.qcut(
#         rfm["Recency"],
#         5,
#         labels= False,
#         duplicates="drop"
#     )
# ##Converse point
#     rfm["R_Score"] = rfm["R_Score"].max() - rfm["R_Score"] + 1

#     rfm["F_Score"] =pd.qcut(
#         rfm["Frequency"],
#         5,
#         labels= False,
#         duplicates= "drop"
#     ) +1 

#     rfm["M_Score"] = pd.qcut(
#         rfm["Monetary"],
#         5,
#         labels=False,
#         duplicates="drop"
#     ) + 1

#     #4. RFM Score
#     rfm["RFM Score"] = (
#         rfm["R_Score"].astype(str)
#         + rfm["F_Score"].astype(str)
#         + rfm["M_Score"].astype(str)
#     )
# #5. Segment mapping
#     segment_map = {
#         "Champions": {
#             "555","554","544","545","454","455","445"
#         },
#         "Loyal": {
#             "543","444","435","355","354","345","344","335"
#         },
#         "Potential Loyalist": {
#             "553","551","552","541","542","533","532","531",
#             "452","451","442","441","431","453","433","432",
#             "423","353","352","351","342","341","333","323"
#         },
#         "New Customers": {
#             "512","511","422","421","412","411","311"
#         },
#         "Promising": {
#             "525","524","523","522","521","515","514","513",
#             "425","424","413","414","415","315","314","313"
#         },
#         "Need Attention": {
#             "535","534","443","434","343","334","325","324"
#         },
#         "About To Sleep": {
#             "331","321","312","221","213","231","241","251"
#         },
#         "At Risk": {
#             "255","254","245","244","253","252","243","242",
#             "235","234","225","224","153","152","145","143",
#             "142","135","134","133","125","124"
#         },
#         "Cannot Lose Them": {
#             "155","154","144","214","215","115","114","113"
#         },
#         "Hibernating customers": {
#             "332","322","233","232","223","222","132","123",
#             "122","212","211"
#         },
#         "Lost customers": {
#             "111","112","121","131","141","151"
#         }
#     }

#     def classify_rfm(score):
#         for segment, scores in segment_map.items():
#             if score in scores:
#                 return segment
#         return "Others"
    
#     rfm["Segment"] = rfm["RFM_Score"].apply(classify_rfm)
    
#     return rfm
