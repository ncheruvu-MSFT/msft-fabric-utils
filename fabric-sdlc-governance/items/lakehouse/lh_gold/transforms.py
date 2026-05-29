"""Gold-layer transforms for lh_gold (medallion curated layer).

Pure pandas — runs server-free in CI. Each function takes a dict of raw
DataFrames (silver layer) and returns the gold DataFrame to materialize as
a Delta table in lh_gold/Tables/.

Add a new function here and register it in GOLD_TABLES to publish a new
gold table; the deployment script (build_lh_gold.py) picks it up automatically.
"""
from __future__ import annotations
import pandas as pd


def dim_account(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Account dimension with industry segment tier."""
    a = silver["accounts"].copy()
    a["revenue_tier"] = pd.cut(
        a["annual_revenue_usd"],
        bins=[0, 50_000_000, 500_000_000, 5_000_000_000, float("inf")],
        labels=["SMB", "MidMarket", "Enterprise", "Strategic"],
    )
    return a


def dim_sales_rep(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Sales rep dimension with tenure (years)."""
    r = silver["sales_reps"].copy()
    r["hire_date"] = pd.to_datetime(r["hire_date"])
    r["tenure_years"] = ((pd.Timestamp.utcnow().tz_localize(None) - r["hire_date"]).dt.days / 365.25).round(1)
    return r


def fact_pipeline_by_stage(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Open pipeline value grouped by stage."""
    o = silver["opportunities"]
    open_opps = o[~o["stage"].isin(["ClosedWon", "ClosedLost"])]
    g = open_opps.groupby("stage", as_index=False).agg(
        open_opps=("opportunity_id", "count"),
        total_amount=("amount", "sum"),
        avg_amount=("amount", "mean"),
    )
    g["total_amount"] = g["total_amount"].round(2)
    g["avg_amount"] = g["avg_amount"].round(2)
    return g


def fact_revenue_by_quarter(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Closed-won revenue rolled up by quarter."""
    fs = silver["fact_sales"]
    g = fs.groupby("quarter", as_index=False).agg(
        deals_won=("sale_id", "count"),
        revenue_usd=("amount", "sum"),
    )
    g["revenue_usd"] = g["revenue_usd"].round(2)
    return g.sort_values("quarter")


def fact_rep_performance(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Quota attainment per rep per quarter."""
    q  = silver["fact_quota"]
    fs = silver["fact_sales"].rename(columns={"rep_id": "rep_id", "amount": "revenue"})
    actuals = fs.groupby(["rep_id", "quarter"], as_index=False).agg(actual=("revenue", "sum"))
    merged  = q.merge(actuals, on=["rep_id", "quarter"], how="left").fillna({"actual": 0})
    merged["attainment_pct"] = (merged["actual"] / merged["quota_amount"] * 100).round(1)
    reps = silver["sales_reps"][["rep_id", "full_name", "region", "segment"]]
    return merged.merge(reps, on="rep_id", how="left")


def fact_account_pipeline(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Top-line account view: open pipeline + won revenue per account."""
    o  = silver["opportunities"]
    a  = silver["accounts"]
    open_  = o[~o["stage"].isin(["ClosedWon", "ClosedLost"])] \
        .groupby("account_id", as_index=False).agg(open_pipeline=("amount", "sum"))
    won    = o[o["stage"] == "ClosedWon"] \
        .groupby("account_id", as_index=False).agg(won_revenue=("amount", "sum"))
    out = a[["account_id", "account_name", "industry", "country"]] \
        .merge(open_, on="account_id", how="left") \
        .merge(won, on="account_id", how="left") \
        .fillna({"open_pipeline": 0, "won_revenue": 0})
    out["open_pipeline"] = out["open_pipeline"].round(2)
    out["won_revenue"]   = out["won_revenue"].round(2)
    return out.sort_values("won_revenue", ascending=False)


def fact_lead_funnel(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Lead funnel summary by source."""
    l = silver["leads"]
    g = l.groupby("source", as_index=False).agg(
        total_leads=("lead_id", "count"),
        qualified=("lead_score", lambda s: int((s >= 70).sum())),
        converted=("converted", "sum"),
    )
    g["qualification_rate_pct"] = (g["qualified"]  / g["total_leads"] * 100).round(1)
    g["conversion_rate_pct"]    = (g["converted"] / g["total_leads"] * 100).round(1)
    return g


GOLD_TABLES = {
    "dim_account":             dim_account,
    "dim_sales_rep":           dim_sales_rep,
    "fact_pipeline_by_stage":  fact_pipeline_by_stage,
    "fact_revenue_by_quarter": fact_revenue_by_quarter,
    "fact_rep_performance":    fact_rep_performance,
    "fact_account_pipeline":   fact_account_pipeline,
    "fact_lead_funnel":        fact_lead_funnel,
}
