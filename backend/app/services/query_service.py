import pandas as pd
import os
from datetime import date

# Load data once at startup
DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/analytics_data.csv")

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    return df

def get_period_data(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    return df[mask]

def compute_topline(
    df: pd.DataFrame,
    baseline_start: str,
    baseline_end: str,
    comparison_start: str,
    comparison_end: str,
    numerator: str,
    denominator: str
) -> dict:
    baseline_df = get_period_data(df, baseline_start, baseline_end)
    comparison_df = get_period_data(df, comparison_start, comparison_end)

    baseline_num = baseline_df[numerator].sum()
    baseline_den = baseline_df[denominator].sum()
    baseline_value = baseline_num / baseline_den if baseline_den > 0 else 0

    comparison_num = comparison_df[numerator].sum()
    comparison_den = comparison_df[denominator].sum()
    comparison_value = comparison_num / comparison_den if comparison_den > 0 else 0

    absolute_delta = comparison_value - baseline_value
    percent_delta = (absolute_delta / baseline_value * 100) if baseline_value > 0 else 0

    return {
        "baseline_value": round(baseline_value, 4),
        "comparison_value": round(comparison_value, 4),
        "absolute_delta": round(absolute_delta, 4),
        "percent_delta": round(percent_delta, 2),
        "baseline_numerator": int(baseline_num),
        "baseline_denominator": int(baseline_den),
        "comparison_numerator": int(comparison_num),
        "comparison_denominator": int(comparison_den)
    }

def compute_segment_breakdown(
    df: pd.DataFrame,
    baseline_start: str,
    baseline_end: str,
    comparison_start: str,
    comparison_end: str,
    numerator: str,
    denominator: str,
    dimension: str
) -> list[dict]:
    baseline_df = get_period_data(df, baseline_start, baseline_end)
    comparison_df = get_period_data(df, comparison_start, comparison_end)

    baseline_grouped = baseline_df.groupby(dimension).agg(
        num=(numerator, "sum"),
        den=(denominator, "sum")
    ).reset_index()
    baseline_grouped["rate"] = baseline_grouped["num"] / baseline_grouped["den"].where(
        baseline_grouped["den"] > 0
    )

    comparison_grouped = comparison_df.groupby(dimension).agg(
        num=(numerator, "sum"),
        den=(denominator, "sum")
    ).reset_index()
    comparison_grouped["rate"] = comparison_grouped["num"] / comparison_grouped["den"].where(
        comparison_grouped["den"] > 0
    )

    total_baseline_den = baseline_grouped["den"].sum()
    total_comparison_den = comparison_grouped["den"].sum()

    merged = pd.merge(
        baseline_grouped, comparison_grouped,
        on=dimension, how="outer", suffixes=("_base", "_comp")
    )
    merged = merged.fillna({
        "num_base": 0,
        "den_base": 0,
        "rate_base": 0,
        "num_comp": 0,
        "den_comp": 0,
        "rate_comp": 0,
    })
    merged["delta"] = merged["rate_comp"] - merged["rate_base"]
    merged["pct_delta"] = (
        (merged["delta"] / merged["rate_base"].where(merged["rate_base"] != 0)) * 100
    ).round(2)

    if total_baseline_den > 0:
        merged["baseline_contribution"] = merged["num_base"] / total_baseline_den
    else:
        merged["baseline_contribution"] = 0

    if total_comparison_den > 0:
        merged["comparison_contribution"] = merged["num_comp"] / total_comparison_den
    else:
        merged["comparison_contribution"] = 0

    merged["contribution_delta"] = (
        merged["comparison_contribution"] - merged["baseline_contribution"]
    )

    results = []
    for _, row in merged.iterrows():
        results.append({
            "segment": row[dimension],
            "baseline_rate": round(row["rate_base"], 4),
            "comparison_rate": round(row["rate_comp"], 4),
            "delta": round(row["delta"], 4),
            "pct_delta": None if pd.isna(row["pct_delta"]) else round(row["pct_delta"], 2),
            "contribution_delta": round(row["contribution_delta"], 6),
        })

    return sorted(results, key=lambda x: abs(x["contribution_delta"]), reverse=True)
