#---Task 1: Load and inspect---#

import pandas as pd
import numpy as np

customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
orders = pd.read_csv("orders.csv")

print("customers:", customers.shape)
print("products:", products.shape)
print("orders.shape =", orders.shape)   # (180, 9)
print(orders.head())
print(orders.isnull().sum())

raw = orders.merge(products, on="product_id")
raw["order_value"] = raw["quantity"] * raw["price"] * (1 - raw["discount_pct"].fillna(0) / 100)
raw_total = round(raw["order_value"].sum(), 2)
print("Raw total revenue:", raw_total)   # 99860.2



#---Task 2: Standardize payment_method---#

print("Before:", orders["payment_method"].unique())
print("Distinct before:", orders["payment_method"].nunique())   # 7

orders["payment_method"] = orders["payment_method"].str.strip().str.upper()

print("After:")
print(orders["payment_method"].value_counts())   # CARD 70, UPI 55, COD 55




#---Task 3: Remove duplicates---#

key = ["customer_id", "product_id", "order_date", "quantity",
       "discount_pct", "payment_method", "rating", "returned"]

dup_mask = orders.duplicated(subset=key, keep="first")
dropped = orders[dup_mask]

print("Rows flagged:", dup_mask.sum())                  # 5
print("Dropped order_ids:", dropped["order_id"].tolist())   # O0176 to O0180

orders_clean = orders[~dup_mask].copy()
print("orders_clean.shape =", orders_clean.shape)       # (175, 9)




#---Task 4: Impute missing values---#

n_disc = orders_clean["discount_pct"].isnull().sum()
orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)
print("discount_pct filled:", n_disc)                   # 12

median_rating = orders_clean["rating"].median()
n_rat = orders_clean["rating"].isnull().sum()
print("Median rating:", median_rating)                  # 3.0
orders_clean["rating"] = orders_clean["rating"].fillna(median_rating)
print("rating filled:", n_rat)                          # 15

print(orders_clean[["discount_pct", "rating"]].isnull().sum())   # 0 and 0




#---Task 5: Merge and reconcile---#

merged = orders_clean.merge(products, on="product_id").merge(customers, on="customer_id")
merged["order_value"] = merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)

cleaned_total = round(merged["order_value"].sum(), 2)
print("Cleaned total:", cleaned_total)                  # 97358.3
# raw_total = 99860.20
# Value of the 5 dropped duplicates, summed independently
dropped_val = dropped.merge(products, on="product_id")
dup_sum = round((dropped_val["quantity"] * dropped_val["price"]
                 * (1 - dropped_val["discount_pct"].fillna(0) / 100)).sum(), 2)
delta = round(raw_total - cleaned_total, 2)
print("Delta:", delta, "| Duplicates' value:", dup_sum)   # both 2501.9

print(f"""
RECONCILIATION NOTE: The raw SQL total (Report a) is Rs {raw_total:,.2f} and the cleaned
pandas total is Rs {cleaned_total:,.2f}, a difference of Rs {delta:,.2f}. This difference is
entirely due to the 5 duplicate (double-submit) orders {dropped['order_id'].tolist()} removed
in Task 3, whose combined order_value, summed independently, is Rs {dup_sum:,.2f}. It is NOT
caused by imputation: filling a missing discount with 0 is the same as the COALESCE(...,0)
used in the raw SQL total, and rating is not part of order_value.
""")




#---Task 6: IQR outliers on quantity---#

q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr
print("Q1:", q1, "Q3:", q3, "IQR:", iqr, "lower:", lower, "upper:", upper)

merged["is_outlier"] = (merged["quantity"] < lower) | (merged["quantity"] > upper)
print(merged[merged["is_outlier"]][["order_id", "quantity", "order_date"]])   # O0011, O0098



#---Task 7: COD hypothesis---#

print("Hypothesis: COD orders have a higher return rate than Card or UPI orders.")

pay = merged.groupby("payment_method")["returned"].agg(["count", "mean"])
pay["return_rate_pct"] = (pay["mean"] * 100).round(1)
print(pay)

rates = pay["return_rate_pct"]
if rates["COD"] > rates["CARD"] and rates["COD"] > rates["UPI"]:
    print("Hypothesis: Confirmed")
else:
    print("Hypothesis: Rejected")




#---Task 8: Segmentation---#

seg = merged.groupby(["payment_method", "city_tier"])["returned"].agg(["count", "mean"])
seg["return_rate_pct"] = (seg["mean"] * 100).round(1)
print(seg)

top = seg["return_rate_pct"].idxmax()        # (payment_method, city_tier)
top_pm = top[0]
top_tier = int(top[1])
top_rate = float(seg.loc[top, "return_rate_pct"])

print(f"HIGHEST-RISK SEGMENT: {top_pm} + Tier-{top_tier} cities at {top_rate}%")
print("COD Tier-1:", seg.loc[("COD", 1), "return_rate_pct"], "%  vs  COD Tier-2:",
      seg.loc[("COD", 2), "return_rate_pct"], "%")
print("COD risk is not uniform across city tiers.")





#---Task 9: Correlation---#

cols = ["rating", "returned", "discount_pct", "quantity"]
corr = merged[cols].corr()
print(corr.round(3))

for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        r = corr.loc[cols[i], cols[j]]
        if abs(r) < 0.2:
            label = "negligible"
        elif abs(r) < 0.4:
            label = "weak"
        elif abs(r) < 0.7:
            label = "moderate"
        else:
            label = "strong"
        print(cols[i], "vs", cols[j], ": r =", round(r, 3), "->", label)

r = corr.loc["discount_pct", "returned"]
print("'Higher discounts reduce returns': r =", round(r, 3), "->",
      "Busted" if abs(r) < 0.2 else "Supported")




#---Task 10: Outlier-corrected time series---#


merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["month"] = merged["order_date"].dt.strftime("%Y-%m")

monthly_all = merged.groupby("month")["order_value"].sum().round(2)
monthly_corr = merged[~merged["is_outlier"]].groupby("month")["order_value"].sum().round(2)

print("(1) Including outliers:")
print(monthly_all)
print("\n(2) Outlier-corrected:")
print(monthly_corr)

infl_month = monthly_all.idxmax()      # 2026-01
peak_month = monthly_corr.idxmax()     # 2026-03

print(f"""
NOTE: {infl_month}'s apparent lead (Rs {monthly_all[infl_month]:,.2f}) is an artifact of the two
bulk orders landing in January (O0011 on 2026-01-28, O0098 on 2026-01-10). Excluding them,
January falls to Rs {monthly_corr[infl_month]:,.2f}, and March ({peak_month}, Rs {monthly_corr[peak_month]:,.2f})
is the genuine peak month.
""")

