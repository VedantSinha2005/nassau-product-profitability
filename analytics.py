"""Transparent, reproducible profitability analytics for the supplied class dataset.

The dataset represents an *assignment case study*, not verified Nassau Candy books.
All currency values are assumed USD as a presentation convention; source has no
explicit currency metadata.
"""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED = {"Row ID", "Order Date", "Division", "Product ID", "Product Name",
            "Sales", "Units", "Gross Profit", "Cost"}
MONETARY_TOLERANCE = 0.011  # cents, including rounding tolerance


def clean_data(source: str | Path | pd.DataFrame):
    """Return validated data and a clear audit trail of exclusions/flags.

    Invalid: missing or nonfinite revenue/cost/profit, Sales <= 0, Cost < 0,
    or failure of the provided Gross Profit = Sales - Cost identity.
    Negative *valid* profit is retained for risk reporting; missing or zero units
    are retained with per-unit measures undefined rather than guessed.
    """
    raw = pd.read_csv(source, encoding="utf-8-sig") if not isinstance(source, pd.DataFrame) else source.copy()
    missing = REQUIRED - set(raw)
    if missing:
        raise ValueError("Dataset missing required columns: " + ", ".join(sorted(missing)))
    d = raw.copy()
    n_input = len(d)
    d["Order Date"] = pd.to_datetime(d["Order Date"], dayfirst=True, errors="coerce")
    for c in ["Sales", "Cost", "Gross Profit", "Units"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ("Division", "Product ID", "Product Name"):
        d[c] = d[c].astype("string").str.strip()
    d["Division"] = d["Division"].str.title()
    # Correct spacing only; do not infer product merges/identities.
    d["Product Name"] = d["Product Name"].str.replace(r"\s*-\s*", " - ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    invalid_date = d["Order Date"].isna()
    invalid_numeric = ~np.isfinite(d[["Sales", "Cost", "Gross Profit"]].to_numpy(dtype=float)).all(axis=1)
    invalid_economics = (d["Sales"] <= 0) | (d["Cost"] < 0)
    inconsistent_profit = ((d["Sales"] - d["Cost"] - d["Gross Profit"]).abs() > MONETARY_TOLERANCE).fillna(False)
    invalid_label = d[["Division", "Product ID", "Product Name"]].isna().any(axis=1) | d[["Division", "Product ID", "Product Name"]].eq("").any(axis=1)
    invalid_mask = invalid_date | invalid_numeric | invalid_economics | inconsistent_profit | invalid_label
    clean = d.loc[~invalid_mask].copy()
    clean["Units"] = clean["Units"].where(clean["Units"] > 0)
    clean["Month"] = clean["Order Date"].dt.to_period("M").dt.to_timestamp()
    clean["Year"] = clean["Order Date"].dt.year
    clean["Row Margin (%)"] = clean["Gross Profit"] / clean["Sales"] * 100
    audit = {
        "source_rows": n_input, "retained_rows": len(clean), "excluded_rows": int(invalid_mask.sum()),
        "invalid_dates": int(invalid_date.sum()),
        "invalid_financial_values": int(invalid_numeric.sum()),
        "nonpositive_sales_or_negative_cost": int(invalid_economics.fillna(False).sum()),
        "inconsistent_gross_profit": int(inconsistent_profit.sum()),
        "missing_product_or_division": int(invalid_label.sum()),
        "missing_or_nonpositive_units_retained": int(clean["Units"].isna().sum()),
        "negative_profit_rows_retained": int((clean["Gross Profit"] < 0).sum()),
        "unique_order_ids": int(clean["Order ID"].nunique()) if "Order ID" in clean else None,
    }
    return clean, audit


def summary(d: pd.DataFrame) -> dict:
    r, c, p, u = (float(d[x].sum()) for x in ("Sales", "Cost", "Gross Profit", "Units"))
    return {"revenue": r, "cost": c, "profit": p, "units": u,
            "gross_margin_pct": 100*p/r if r else np.nan,
            "profit_per_unit": p/u if u else np.nan,
            "products": int(d["Product ID"].nunique()), "divisions": int(d["Division"].nunique()),
            "rows": int(len(d))}


def product_metrics(d: pd.DataFrame) -> pd.DataFrame:
    cols = ["Product ID", "Product Name", "Division"]
    g = d.groupby(cols, as_index=False, dropna=False).agg(
        Revenue=("Sales", "sum"), Cost=("Cost", "sum"),
        Profit=("Gross Profit", "sum"), Units=("Units", "sum"),
        Transactions=("Sales", "size"), Active_Months=("Month", "nunique"))
    rev_total = g.Revenue.sum(); profit_total = g.Profit.sum()
    g["Gross Margin (%)"] = np.where(g.Revenue > 0, 100*g.Profit/g.Revenue, np.nan)
    g["Profit/Unit"] = np.where(g.Units > 0, g.Profit/g.Units, np.nan)
    g["Revenue Contribution (%)"] = 100*g.Revenue/rev_total if rev_total else np.nan
    g["Profit Contribution (%)"] = 100*g.Profit/profit_total if profit_total else np.nan
    m = d.groupby(["Product ID", "Month"], as_index=False).agg(revenue=("Sales","sum"), profit=("Gross Profit","sum"))
    m["monthly_margin"] = np.where(m.revenue > 0, 100*m.profit/m.revenue, np.nan)
    # Diagnostic, not variance of transaction-level margins. Requires >= 2 months.
    vol = m.groupby("Product ID")["monthly_margin"].agg(lambda x: float(x.std(ddof=1)) if x.notna().sum()>1 else np.nan)
    g["Margin Volatility (pp)"] = g["Product ID"].map(vol).fillna(np.nan)
    return g.sort_values(["Profit", "Product Name"], ascending=[False, True]).reset_index(drop=True)


def division_metrics(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("Division", as_index=False).agg(Revenue=("Sales", "sum"), Cost=("Cost", "sum"), Profit=("Gross Profit", "sum"), Units=("Units", "sum"), Transactions=("Sales", "size"), Products=("Product ID", "nunique"))
    g["Gross Margin (%)"] = np.where(g.Revenue>0, g.Profit/g.Revenue*100, np.nan)
    g["Revenue Contribution (%)"] = 100*g.Revenue/g.Revenue.sum()
    g["Profit Contribution (%)"] = 100*g.Profit/g.Profit.sum() if g.Profit.sum() else np.nan
    return g.sort_values("Profit", ascending=False).reset_index(drop=True)


def profit_pareto(p: pd.DataFrame, metric="Profit") -> pd.DataFrame:
    """Sort positive values; optionally compute 80%-threshold for net profit.
    Negative values remain separate and are not quietly reallocated.
    """
    ordered = p.sort_values(metric, ascending=False).copy()
    total = ordered[metric].sum()
    ordered["Cumulative Share (%)"] = ordered[metric].cumsum()/total*100 if total>0 else np.nan
    ordered["Product Rank"] = np.arange(1, len(ordered)+1)
    return ordered


def products_to_80_pct(p: pd.DataFrame, metric="Profit") -> int | None:
    q = profit_pareto(p,metric)
    if q.empty or not np.isfinite(q["Cumulative Share (%)"].to_numpy()).any():
        return None
    hits = q.loc[q["Cumulative Share (%)"]>=80]
    return int(hits["Product Rank"].iloc[0]) if not hits.empty else None


def risk_flags(p: pd.DataFrame, margin_threshold=50.0, min_revenue=1000.0) -> pd.DataFrame:
    q = p.copy()
    q["Low Margin"] = q["Gross Margin (%)"] < margin_threshold
    q["Material Revenue"] = q.Revenue >= min_revenue
    q["High Sales / Low Margin"] = q["Low Margin"] & (q.Revenue >= q.Revenue.quantile(0.75))
    q["Risk Classification"] = np.select(
        [q["Low Margin"] & q["Material Revenue"], q["Low Margin"], q["High Sales / Low Margin"]],
        ["Priority margin review", "Low margin - smaller exposure", "High sales / low margin"],default="Monitor")
    # override high-sales on top of margin and material risk
    q.loc[q["High Sales / Low Margin"], "Risk Classification"] = "High sales / low margin"
    return q


def monthly_metrics(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("Month", as_index=False).agg(Revenue=("Sales", "sum"), Cost=("Cost", "sum"), Profit=("Gross Profit", "sum"), Units=("Units", "sum"))
    g["Gross Margin (%)"] = 100*g.Profit/g.Revenue
    return g.sort_values("Month")
