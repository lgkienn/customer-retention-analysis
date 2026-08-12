# Data Dictionary — Online Retail (UK Gift E-commerce)

> Source: UCI Machine Learning Repository — "Online Retail" (Chen, D., 2015).
> A UK-based, registered non-store online retailer selling all-occasion giftware,
> with a large wholesale customer base. Public dataset, used here to simulate a
> realistic customer-analytics engagement.

---

## Table: `ecommerce_retail` (raw transaction log)

**Grain:** 1 row = 1 product line within an invoice
**Row count (raw):** 541,909
**Period:** 2010-12-01 → 2011-12-09 (~12 months)

| Column | Type | Description | Example | Nullable | Notes |
|---|---|---|---|---|---|
| `InvoiceNo` | VARCHAR | Invoice/transaction identifier. 6-digit number. A `C` prefix marks a **cancellation/return**. | `536365` / `C536379` | No | ~9.3k rows are cancellations |
| `StockCode` | VARCHAR | Product code. Usually a 5-digit number, sometimes with a letter suffix. Non-product codes exist. | `85123A` | No | Non-product codes: `POST`, `D`, `C2`, `DOT`, `M`, `BANK CHARGES`, `S`, `AMAZONFEE` |
| `Description` | VARCHAR | Product name (free text, ALL CAPS). | `WHITE HANGING HEART T-LIGHT HOLDER` | Yes | 1,454 nulls |
| `Quantity` | INT | Units per line. **Negative** on returns/cancellations. | `6` | No | Raw range −80,995 → 80,995 |
| `InvoiceDate` | DATETIME | Timestamp the invoice was generated. | `2010-12-01 08:26:00` | No | |
| `UnitPrice` | DECIMAL | List price per unit, in **GBP (£)**. Some rows are 0 or negative (adjustments). | `2.55` | No | Raw range −11,062 → 38,970 |
| `CustomerID` | INT (stored as float) | Customer identifier. **Null = guest / unregistered checkout.** | `17850` | Yes | 135,080 nulls (~25%) |
| `Country` | VARCHAR | Country of the customer. | `United Kingdom` | No | 38 countries; UK ≈ 85% of revenue |

---

## Derived fields (created in cleaning)

| Field | Formula | Purpose |
|---|---|---|
| `ValidStockCode` | `StockCode` matches `^\d{5}.*` | Flag true product lines vs fees/postage/adjustments |
| `CustomerType` | `Guest` if `CustomerID` is null else `Registered` | Separate identifiable customers from guest checkout |
| `Revenue` | `Quantity × UnitPrice` (GBP) | Line-level revenue. This is **gross list revenue** — the dataset has no discount field |

---

## Cleaning summary (raw → analysis-ready)

| Step | Rows removed | Rows remaining |
|---|---|---|
| Raw | — | 541,909 |
| Remove cancellations (`InvoiceNo` starts with `C`) | 9,288 | 532,621 |
| Keep only valid 5-digit product codes | 2,411 | 530,210 |
| **Analysis-ready** | | **530,210** |

Of the 530,210 clean rows: **396,370 Registered** / **133,840 Guest**.

---

## Known data-quality notes (be transparent in README)

- **Revenue = list price × quantity.** There is no cost or discount column, so margin/profit analysis is **out of scope** for this dataset. All findings are revenue/behaviour based.
- **2,485 zero-price rows** remain after cleaning (products that never had a positive price to back-fill from). They contribute £0 and do not affect revenue.
- **RFM is computed on Registered customers only** — guests have no `CustomerID`, so they cannot be tracked across visits.
- **Analysis snapshot date = 2011-12-31.** The data ends 2011-12-09, so the final partial month (Dec 2011) and the newest cohorts have a **truncated observation window** — retention for the last 1–2 cohorts is understated.
