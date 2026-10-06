"""Python Data Analysis Application
Pipeline: load -> clean -> analyze -> visualize -> fetch API data -> report.
Libraries: NumPy, Pandas, Matplotlib, Seaborn, requests.
"""
import os
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # works without a display (also fine in Colab)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns

DATA_PATH = "sales_data.csv"
OUTPUT_DIR = "output"
API_BASE = "https://jsonplaceholder.typicode.com"


# ------------------------------------------------------------------
# 1. Dataset (generate a messy sample so the project runs anywhere)
# ------------------------------------------------------------------
def generate_sample_dataset(path=DATA_PATH, n=300, seed=42):
    """Create a realistic, intentionally messy sales dataset."""
    rng = np.random.default_rng(seed)
    products = {
        "Electronics": [("Laptop", 55000), ("Headphones", 2500), ("Smartphone", 22000)],
        "Clothing": [("T-Shirt", 600), ("Jeans", 1800), ("Jacket", 3500)],
        "Home": [("Mixer", 3200), ("Lamp", 900), ("Cushion", 450)],
        "Books": [("Python Book", 550), ("Novel", 350), ("Notebook", 120)],
    }
    rows = []
    for i in range(n):
        category = rng.choice(list(products))
        product, price = products[category][rng.integers(0, 3)]
        rows.append({
            "order_id": 1000 + i,
            "order_date": pd.Timestamp("2026-01-01") + pd.Timedelta(days=int(rng.integers(0, 270))),
            "customer": f"Customer_{rng.integers(1, 60)}",
            "region": rng.choice(["North", "South", "East", "West"]),
            "category": category,
            "product": product,
            "quantity": int(rng.integers(1, 8)),
            "unit_price": price * rng.uniform(0.9, 1.1),
            "discount": rng.choice([0, 0.05, 0.1, 0.2]),
        })
    df = pd.DataFrame(rows)

    # introduce mess: missing values, duplicates, bad casing/spaces, outlier, bad date
    df.loc[rng.choice(n, 12, replace=False), "quantity"] = np.nan
    df.loc[rng.choice(n, 10, replace=False), "region"] = None
    df.loc[rng.choice(n, 15, replace=False), "category"] = df["category"].str.upper()
    df.loc[rng.choice(n, 10, replace=False), "region"] = "  north "
    df.loc[5, "quantity"] = 500  # outlier
    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    df.loc[3, "order_date"] = "not a date"
    df = pd.concat([df, df.sample(8, random_state=1)], ignore_index=True)  # duplicates
    df.to_csv(path, index=False)
    return path


def load_data(path=DATA_PATH):
    """Load the CSV, generating the sample dataset if it doesn't exist."""
    if not os.path.exists(path):
        print(f"{path} not found - generating sample dataset...")
        generate_sample_dataset(path)
    df = pd.read_csv(path)
    print(f"Loaded {df.shape[0]} rows x {df.shape[1]} columns")
    return df


# ------------------------------------------------------------------
# 2. Cleaning
# ------------------------------------------------------------------
def clean_data(df):
    """Return (clean_df, log) where log records what was fixed."""
    log = {"rows_before": len(df)}
    df = df.copy()

    log["duplicates_removed"] = int(df.duplicated().sum())
    df = df.drop_duplicates()

    for col in ["region", "category", "product", "customer"]:
        df[col] = df[col].astype("string").str.strip().str.title()

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    log["bad_dates_removed"] = int(df["order_date"].isna().sum())
    df = df.dropna(subset=["order_date"])

    log["missing_region_filled"] = int(df["region"].isna().sum())
    df["region"] = df["region"].fillna("Unknown")

    log["missing_quantity_filled"] = int(df["quantity"].isna().sum())
    df["quantity"] = df["quantity"].fillna(df["quantity"].median())

    # remove outliers in quantity using the IQR rule
    q1, q3 = df["quantity"].quantile([0.25, 0.75])
    upper = q3 + 1.5 * (q3 - q1)
    outliers = df["quantity"] > upper
    log["outliers_removed"] = int(outliers.sum())
    df = df[~outliers]

    df["quantity"] = df["quantity"].astype(int)
    df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
    df["month"] = df["order_date"].dt.to_period("M").astype(str)

    log["rows_after"] = len(df)
    return df.reset_index(drop=True), log


# ------------------------------------------------------------------
# 3. Analysis
# ------------------------------------------------------------------
def analyze(df):
    """Compute key business metrics and return them in a dict."""
    results = {
        "total_revenue": df["revenue"].sum(),
        "avg_order_value": df["revenue"].mean(),
        "median_order_value": float(np.median(df["revenue"])),
        "std_order_value": float(np.std(df["revenue"])),
        "p90_order_value": float(np.percentile(df["revenue"], 90)),
        "orders": len(df),
        "by_category": df.groupby("category")["revenue"].sum().sort_values(ascending=False),
        "by_region": df.groupby("region")["revenue"].sum().sort_values(ascending=False),
        "top_products": df.groupby("product")["revenue"].sum().nlargest(5),
        "monthly": df.groupby("month")["revenue"].sum(),
        "top_customers": df.groupby("customer")["revenue"].sum().nlargest(5),
        "correlation": df[["quantity", "unit_price", "discount", "revenue"]].corr(),
    }
    return results


# ------------------------------------------------------------------
# 4. Visualization
# ------------------------------------------------------------------
def create_plots(df, results, out_dir=OUTPUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")
    paths = []

    # Monthly revenue trend
    fig, ax = plt.subplots(figsize=(9, 4))
    results["monthly"].plot(marker="o", ax=ax)
    ax.set(title="Monthly Revenue", xlabel="Month", ylabel="Revenue")
    plt.xticks(rotation=45)
    paths.append(_save(fig, out_dir, "monthly_revenue.png"))

    # Revenue by category
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.barplot(x=results["by_category"].index, y=results["by_category"].values, ax=ax)
    ax.set(title="Revenue by Category", xlabel="", ylabel="Revenue")
    paths.append(_save(fig, out_dir, "revenue_by_category.png"))

    # Order value distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(df["revenue"], bins=30, kde=True, ax=ax)
    ax.set(title="Distribution of Order Value", xlabel="Revenue")
    paths.append(_save(fig, out_dir, "order_distribution.png"))

    # Correlation heatmap
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(results["correlation"], annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Correlation Heatmap")
    paths.append(_save(fig, out_dir, "correlation_heatmap.png"))

    return paths


def _save(fig, out_dir, name):
    path = os.path.join(out_dir, name)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# ------------------------------------------------------------------
# 5. REST API consumption (JSON)
# ------------------------------------------------------------------
def fetch_json(endpoint, timeout=10):
    """GET a JSON payload from the API; returns [] on failure."""
    url = f"{API_BASE}/{endpoint}"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed for {url}: {e}")
        return []


def api_summary():
    """Fetch users and posts, then compute posts per user with Pandas."""
    users = fetch_json("users")
    posts = fetch_json("posts")
    if not users or not posts:
        return None
    users_df = pd.json_normalize(users)[["id", "name", "email", "company.name"]]
    posts_df = pd.DataFrame(posts)
    counts = posts_df.groupby("userId").size().rename("post_count").reset_index()
    merged = users_df.merge(counts, left_on="id", right_on="userId")
    return merged[["name", "company.name", "post_count"]]


# ------------------------------------------------------------------
# 6. Report generation
# ------------------------------------------------------------------
def generate_report(df, log, results, plot_paths, api_df, out_dir=OUTPUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    lines = [
        "# Data Analysis Report",
        f"_Generated on {datetime.now():%Y-%m-%d %H:%M}_\n",
        "## 1. Data Cleaning Summary",
        *[f"- {k.replace('_', ' ').title()}: {v}" for k, v in log.items()],
        "\n## 2. Key Metrics",
        f"- Total revenue: {results['total_revenue']:,.2f}",
        f"- Orders: {results['orders']}",
        f"- Average order value: {results['avg_order_value']:,.2f}",
        f"- Median order value: {results['median_order_value']:,.2f}",
        f"- Std deviation: {results['std_order_value']:,.2f}",
        f"- 90th percentile order value: {results['p90_order_value']:,.2f}",
        "\n## 3. Revenue by Category",
        results["by_category"].round(2).to_markdown(),
        "\n## 4. Revenue by Region",
        results["by_region"].round(2).to_markdown(),
        "\n## 5. Top 5 Products",
        results["top_products"].round(2).to_markdown(),
        "\n## 6. Top 5 Customers",
        results["top_customers"].round(2).to_markdown(),
        "\n## 7. Charts",
        *[f"![{os.path.basename(p)}]({os.path.basename(p)})" for p in plot_paths],
        "\n## 8. API Data (JSONPlaceholder)",
        api_df.to_markdown(index=False) if api_df is not None else "_API data unavailable (no internet)._",
    ]
    path = os.path.join(out_dir, "report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


# ------------------------------------------------------------------
def main():
    raw = load_data()
    clean, log = clean_data(raw)
    clean.to_csv(os.path.join(OUTPUT_DIR, "cleaned_data.csv"), index=False) if os.makedirs(OUTPUT_DIR, exist_ok=True) is None else None
    results = analyze(clean)
    plots = create_plots(clean, results)
    api_df = api_summary()
    report = generate_report(clean, log, results, plots, api_df)
    print(f"Done. Report saved to {report}")


if __name__ == "__main__":
    main()