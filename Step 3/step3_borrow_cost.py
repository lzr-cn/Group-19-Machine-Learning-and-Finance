"""Step 3 - Filtering the short leg for borrow cost (Section 4 of the brief).

This module builds a point-in-time hard-to-borrow (HTB) proxy on the Stage 2
trade-eligible universe and maps it onto the three-tier borrow-cost schedule of
Section 6.3 / 6.4 of the C2O coursework brief:

    Tier A - General Collateral ............  40 bps p.a.   (not hard-to-borrow)
    Tier B - mid-tier specials .............  200 bps p.a.  (moderate confidence)
    Tier C - deep specials .................  800 bps p.a.  (high confidence)

Inputs (produced by Stage 1 / Stage 2, see README_STAGE3_CN.md):
    stage2_capacity_eligibility.parquet              - per (stock, date) eligibility
    stage1_short_interest_daily_from_stage1_2.parquet - daily, lagged short interest

The short-interest series is already point-in-time: Stage 1 applied the FINRA
publication lag plus the additional 2-day vendor-delivery lag of Section 2.1.3
and forward-filled between bi-monthly releases, so every (stock, date) value here
is observable to a trader at 15:50 ET on that date.

Output: per (stock, date) borrow-tier table + summaries + figures, ready for the
Stage 5 back-test to charge borrow daily on the gross short notional.

Run:  python step3_borrow_cost.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #
STAGE2_DIR = Path("stage2_outputs_from_stage1_2")
OUT_DIR = Path("step3_outputs")

# Section 6.3 borrow schedule - these rates are fixed by the brief.
BORROW_RATE_A = 40.0   # bps p.a. - General Collateral
BORROW_RATE_B = 200.0  # bps p.a. - mid-tier specials
BORROW_RATE_C = 800.0  # bps p.a. - deep specials
TRADING_DAYS = 252.0

# --- Hard-to-borrow proxy thresholds -------------------------------------- #
# Absolute economic gates, justified against the cross-sectional distribution
# of the Stage 2 eligible pool (dsi = short interest / shares outstanding,
# dtcn = days-to-cover).  Among eligible names: dsi p90 ~ 0.09, p99 ~ 0.20;
# dtcn p90 ~ 9.5, p99 ~ 21.5.  We therefore read:
#   * dsi >= 0.10  ("above 10% of float", the brief's own borrow-risk marker)
#     or dtcn >= 10 (>= ~2 trading weeks to cover) -> hard-to-borrow.
#   * dsi >= 0.20  or dtcn >= 20 (roughly the p99 of each series) -> deep special.
HTB_DSI_FLOOR = 0.10
HTB_DTCN_FLOOR = 10.0
DEEP_DSI_FLOOR = 0.20
DEEP_DTCN_FLOOR = 20.0

# Borrow-stress booster: a name that is already *near* the deep gate and is
# simultaneously in the most acute borrow-stress state of the day (top decile of
# the daily cross-section of ddtcn, the change in days-to-cover, and rising) is
# escalated to Tier C.  Requiring proximity to the deep gate keeps Tier C a
# genuine minority - the booster refines the deep set rather than dominating it.
# The percentile is computed *within each day's cross-section*, so it is
# point-in-time.
STRESS_QUANTILE = 0.90
NEAR_DEEP_DSI = 0.15
NEAR_DEEP_DTCN = 15.0

SEED = 20260531
np.random.seed(SEED)


# --------------------------------------------------------------------------- #
# Load                                                                        #
# --------------------------------------------------------------------------- #
def load_inputs(stage2_dir: Path = STAGE2_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the Stage 2 eligibility table and the daily short-interest table."""
    elig = pd.read_parquet(
        stage2_dir / "stage2_capacity_eligibility.parquet",
        columns=["date", "year", "ticker", "instrument_id", "is_trade_eligible"],
    )
    si = pd.read_parquet(
        stage2_dir / "stage1_short_interest_daily_from_stage1_2.parquet"
    )
    # In the short-interest table, stock_id is the instrument_id used elsewhere.
    si = si.rename(columns={"stock_id": "instrument_id"})
    si["instrument_id"] = si["instrument_id"].astype("int64")
    elig["date"] = pd.to_datetime(elig["date"])
    si["date"] = pd.to_datetime(si["date"])
    return elig, si


# --------------------------------------------------------------------------- #
# Hard-to-borrow proxy + tier assignment                                      #
# --------------------------------------------------------------------------- #
def build_borrow_tiers(elig: pd.DataFrame, si: pd.DataFrame) -> pd.DataFrame:
    """Build the per (stock, date) hard-to-borrow flag and borrow tier.

    Step 3 only treats the *short* leg, so we work on the Stage 2 trade-eligible
    pool (these are the names that may enter either book).  Borrow tiers are
    attached to every eligible (stock, date); the Stage 5 back-test applies the
    charge only on names actually held short.
    """
    base = elig[elig["is_trade_eligible"]].copy()

    df = base.merge(
        si[["date", "instrument_id", "dsi", "dtcn", "ddtcn"]],
        on=["date", "instrument_id"],
        how="left",
    )

    # A tiny fraction (~0.6%) of eligible stock-days have no published short
    # interest yet.  Absent evidence of scarcity, we treat them as General
    # Collateral (the conservative-for-alpha, neutral-for-cost default) and
    # record the reason so it is auditable.
    no_si = df["dsi"].isna()

    dsi = df["dsi"]
    dtcn = df["dtcn"]
    ddtcn = df["ddtcn"]

    # Absolute economic gates.
    htb_abs = (dsi >= HTB_DSI_FLOOR) | (dtcn >= HTB_DTCN_FLOOR)
    deep_abs = (dsi >= DEEP_DSI_FLOOR) | (dtcn >= DEEP_DTCN_FLOOR)

    # Same-day cross-sectional borrow-stress flag (point-in-time): rising
    # days-to-cover in the top decile of the day's eligible cross-section.
    # Defensive against non-finite ddtcn on a re-run over unseen data (the
    # marker re-runs on the held-out window): drop +/-inf before the quantile
    # so the daily stress cutoff is never contaminated. quantile skips NaN.
    day_stress_cut = df.groupby("date")["ddtcn"].transform(
        lambda s: s.replace([np.inf, -np.inf], np.nan).quantile(STRESS_QUANTILE)
    )
    near_deep = (dsi >= NEAR_DEEP_DSI) | (dtcn >= NEAR_DEEP_DTCN)
    acute_stress = (ddtcn > 0) & (ddtcn >= day_stress_cut)

    hard_to_borrow = (htb_abs | deep_abs) & (~no_si)
    deep_special = (deep_abs | (near_deep & acute_stress)) & (~no_si)

    # Tier assignment.
    tier = np.where(deep_special, "C", np.where(hard_to_borrow, "B", "A"))
    df["hard_to_borrow_flag"] = hard_to_borrow.fillna(False).to_numpy()
    escalated_by_stress = near_deep & acute_stress & (~deep_abs) & (~no_si)
    df["borrow_stress_flag"] = escalated_by_stress.fillna(False).to_numpy()
    df["borrow_tier"] = tier
    df["no_short_interest"] = no_si.to_numpy()

    rate_map = {"A": BORROW_RATE_A, "B": BORROW_RATE_B, "C": BORROW_RATE_C}
    df["borrow_rate_annual_bps"] = df["borrow_tier"].map(rate_map)
    # Per-day charge actually applied to a short position (Section 6.4):
    # annual rate / 252.
    df["borrow_cost_daily_bps"] = df["borrow_rate_annual_bps"] / TRADING_DAYS

    cols = [
        "date", "year", "ticker", "instrument_id",
        "dsi", "dtcn", "ddtcn",
        "hard_to_borrow_flag", "borrow_stress_flag", "no_short_interest",
        "borrow_tier", "borrow_rate_annual_bps", "borrow_cost_daily_bps",
    ]
    return df[cols].sort_values(["instrument_id", "date"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Summaries                                                                    #
# --------------------------------------------------------------------------- #
def tier_yearly_summary(tiers: pd.DataFrame) -> pd.DataFrame:
    """Stock-day counts and shares by borrow tier per year."""
    g = tiers.groupby(["year", "borrow_tier"]).size().unstack(fill_value=0)
    for t in ["A", "B", "C"]:
        if t not in g.columns:
            g[t] = 0
    g = g[["A", "B", "C"]]
    g["total"] = g.sum(axis=1)
    g["pct_A"] = (g["A"] / g["total"] * 100).round(2)
    g["pct_B"] = (g["B"] / g["total"] * 100).round(2)
    g["pct_C"] = (g["C"] / g["total"] * 100).round(2)
    g["htb_share_pct"] = ((g["B"] + g["C"]) / g["total"] * 100).round(2)
    return g.reset_index()


def top_htb_names(tiers: pd.DataFrame, n: int = 25) -> pd.DataFrame:
    """Names that spend the most stock-days in Tier C - external-validation aid.

    The report's Section 4 Q2 can sanity-check these against documented
    short-squeeze / hard-to-borrow episodes.
    """
    c = tiers[tiers["borrow_tier"] == "C"]
    out = (
        c.groupby("ticker")
        .agg(
            tier_c_days=("date", "size"),
            mean_dsi=("dsi", "mean"),
            max_dsi=("dsi", "max"),
            mean_dtcn=("dtcn", "mean"),
            first_date=("date", "min"),
            last_date=("date", "max"),
        )
        .sort_values("tier_c_days", ascending=False)
        .head(n)
        .reset_index()
    )
    out["mean_dsi"] = out["mean_dsi"].round(4)
    out["max_dsi"] = out["max_dsi"].round(4)
    out["mean_dtcn"] = out["mean_dtcn"].round(2)
    return out


# --------------------------------------------------------------------------- #
# Figures                                                                      #
# --------------------------------------------------------------------------- #
def plot_tier_evolution(yearly: pd.DataFrame, out_dir: Path) -> Path:
    """Stacked share of the eligible short pool by borrow tier, by year."""
    fig, ax = plt.subplots(figsize=(10, 5))
    years = yearly["year"].to_numpy()
    ax.bar(years, yearly["pct_A"], label="Tier A - GC (40 bps)", color="#2c7fb8")
    ax.bar(years, yearly["pct_B"], bottom=yearly["pct_A"],
           label="Tier B - mid special (200 bps)", color="#f0a202")
    ax.bar(years, yearly["pct_C"], bottom=yearly["pct_A"] + yearly["pct_B"],
           label="Tier C - deep special (800 bps)", color="#d7191c")
    ax.set_ylabel("Share of eligible stock-days (%)")
    ax.set_xlabel("Year")
    ax.set_title(
        "Step 3 - Borrow-tier composition of the eligible universe\n"
        f"(Tier B: dsi>={HTB_DSI_FLOOR} or dtcn>={HTB_DTCN_FLOOR:g}; "
        f"Tier C: dsi>={DEEP_DSI_FLOOR} or dtcn>={DEEP_DTCN_FLOOR:g} "
        "or near-deep + acute stress)"
    )
    ax.legend(loc="lower left", fontsize=9)
    ax.set_ylim(0, 100)
    fig.tight_layout()
    path = out_dir / "step3_tier_evolution.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_htb_share(yearly: pd.DataFrame, out_dir: Path) -> Path:
    """Hard-to-borrow share (Tier B + C) of the eligible universe over time."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(yearly["year"], yearly["htb_share_pct"], marker="o", color="#d7191c")
    ax.set_ylabel("Hard-to-borrow share (%)")
    ax.set_xlabel("Year")
    ax.set_title("Step 3 - Fraction of the eligible universe flagged "
                 "hard-to-borrow (Tier B + Tier C)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = out_dir / "step3_htb_share.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def plot_si_example(si: pd.DataFrame, tiers: pd.DataFrame, out_dir: Path) -> Path:
    """Short-interest series with tier shading for the most-flagged Tier C name."""
    top = top_htb_names(tiers, n=1)
    if top.empty:
        return out_dir / "step3_si_example.png"
    tk = top.loc[0, "ticker"]
    iid = tiers.loc[tiers["ticker"] == tk, "instrument_id"].iloc[0]
    ex = tiers[tiers["instrument_id"] == iid].sort_values("date")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    ax1.plot(ex["date"], ex["dsi"], color="#2c7fb8")
    ax1.axhline(HTB_DSI_FLOOR, ls="--", c="#f0a202", lw=1, label="Tier B floor")
    ax1.axhline(DEEP_DSI_FLOOR, ls="--", c="#d7191c", lw=1, label="Tier C floor")
    ax1.set_ylabel("dsi (SI / shares out)")
    ax1.set_title(f"Step 3 - short interest & borrow tier for {tk} "
                  f"(instrument_id={iid})")
    ax1.legend(fontsize=8)
    colors = {"A": "#2c7fb8", "B": "#f0a202", "C": "#d7191c"}
    ax2.scatter(ex["date"], ex["dtcn"], s=4,
                c=ex["borrow_tier"].map(colors))
    ax2.axhline(HTB_DTCN_FLOOR, ls="--", c="#f0a202", lw=1)
    ax2.axhline(DEEP_DTCN_FLOOR, ls="--", c="#d7191c", lw=1)
    ax2.set_ylabel("dtcn (days to cover)")
    ax2.set_xlabel("Date")
    fig.tight_layout()
    path = out_dir / "step3_si_example.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #
def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    elig, si = load_inputs()

    tiers = build_borrow_tiers(elig, si)
    yearly = tier_yearly_summary(tiers)
    top = top_htb_names(tiers, n=25)

    # Persist outputs.
    tiers.to_parquet(OUT_DIR / "step3_borrow_tiers.parquet", index=False)
    yearly.to_csv(OUT_DIR / "step3_tier_yearly_summary.csv", index=False)
    top.to_csv(OUT_DIR / "step3_top_htb_names.csv", index=False)

    params = {
        "borrow_rate_A_bps": BORROW_RATE_A,
        "borrow_rate_B_bps": BORROW_RATE_B,
        "borrow_rate_C_bps": BORROW_RATE_C,
        "trading_days_per_year": TRADING_DAYS,
        "htb_dsi_floor": HTB_DSI_FLOOR,
        "htb_dtcn_floor": HTB_DTCN_FLOOR,
        "deep_dsi_floor": DEEP_DSI_FLOOR,
        "deep_dtcn_floor": DEEP_DTCN_FLOOR,
        "near_deep_dsi": NEAR_DEEP_DSI,
        "near_deep_dtcn": NEAR_DEEP_DTCN,
        "stress_quantile": STRESS_QUANTILE,
        "seed": SEED,
    }
    with open(OUT_DIR / "step3_parameters.json", "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)

    plot_tier_evolution(yearly, OUT_DIR)
    plot_htb_share(yearly, OUT_DIR)
    plot_si_example(si.rename(columns={}), tiers, OUT_DIR)

    # Console report.
    n = len(tiers)
    shares = tiers["borrow_tier"].value_counts(normalize=True).mul(100).round(2)
    print(f"Step 3 complete. {n:,} eligible stock-days tiered.")
    print("Full-sample tier shares (%):")
    print(shares.to_string())
    htb = (tiers["borrow_tier"] != "A").mean() * 100
    print(f"Hard-to-borrow share (Tier B+C): {htb:.2f}%")
    print(f"No-short-interest stock-days defaulted to Tier A: "
          f"{tiers['no_short_interest'].mean() * 100:.2f}%")
    print(f"\nOutputs written to {OUT_DIR.resolve()}")
    print(top.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
