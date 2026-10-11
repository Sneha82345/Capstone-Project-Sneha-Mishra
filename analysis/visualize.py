import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

# ---------- Load and clean (same steps as clean_and_eda.py) ----------
customers = pd.read_csv("customers.csv")
products = pd.read_csv("products.csv")
orders = pd.read_csv("orders.csv")

orders["payment_method"] = orders["payment_method"].str.strip().str.upper()

key = ["customer_id", "product_id", "order_date", "quantity",
       "discount_pct", "payment_method", "rating", "returned"]
orders_clean = orders[~orders.duplicated(subset=key, keep="first")].copy()

orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)
orders_clean["rating"] = orders_clean["rating"].fillna(orders_clean["rating"].median())

merged = orders_clean.merge(products, on="product_id").merge(customers, on="customer_id")
merged["order_value"] = merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)

# Outliers (IQR on quantity)
q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)
iqr = q3 - q1
merged["is_outlier"] = (merged["quantity"] < q1 - 1.5 * iqr) | (merged["quantity"] > q3 + 1.5 * iqr)

# ---------- Numbers for the charts ----------
rates = (merged.groupby("payment_method")["returned"].mean() * 100).round(1)
rates_sorted = rates.sort_values(ascending=False)

merged["month"] = pd.to_datetime(merged["order_date"]).dt.strftime("%Y-%m")
monthly_corr = merged[~merged["is_outlier"]].groupby("month")["order_value"].sum().round(2)
peak_month = monthly_corr.idxmax()

os.makedirs("visualizations", exist_ok=True)

# ---------- Chart 1 ----------
top = rates_sorted.index[0]
bottom = rates_sorted.index[-1]
ratio = rates_sorted.iloc[0] / rates_sorted.iloc[-1]

plt.figure(figsize=(7, 5))
bars = plt.bar(rates_sorted.index, rates_sorted.values, color=["#d62728", "#7f7f7f", "#7f7f7f"])
for bar, value in zip(bars, rates_sorted.values):
    plt.text(bar.get_x() + bar.get_width() / 2, value + 0.8, f"{value:.1f}%",
             ha="center", fontweight="bold")
plt.title(f"{top} Returns at {rates_sorted.iloc[0]:.1f}% - {ratio:.0f}x {bottom.title()}")
plt.xlabel("Payment method")
plt.ylabel("Return rate (%)")
plt.ylim(0, rates_sorted.max() * 1.2)
plt.tight_layout()
plt.savefig("visualizations/return_rate_by_payment.png", dpi=150)
plt.show()

# ---------- Chart 2 ----------
peak_name = pd.Timestamp(peak_month + "-01").strftime("%B")

plt.figure(figsize=(8, 5))
plt.plot(monthly_corr.index, monthly_corr.values, marker="o", linewidth=2, color="#1f77b4")
plt.annotate(f"Peak: Rs {monthly_corr[peak_month]:,.2f}",
             (peak_month, monthly_corr[peak_month]),
             textcoords="offset points", xytext=(0, 12), ha="center", fontweight="bold")
plt.title(f"Outlier-Corrected Revenue Peaks in {peak_name} ({peak_month})")
plt.xlabel("Month")
plt.ylabel("Revenue (INR, outliers excluded)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("visualizations/monthly_revenue_trend.png", dpi=150)
plt.show()

print("Saved: visualizations/return_rate_by_payment.png")
print("Saved: visualizations/monthly_revenue_trend.png")
