"""Stage 5 - From ranking to portfolio, with realistic costs (C2O coursework, Section 6).

This module turns the Stage-4 cross-sectional scores (Ridge + XGBoost2) into a daily,
dollar-neutral, market-neutral overnight long/short portfolio and back-tests it under the
fixed Section 6.3 cost schedule, at the three required portfolio-AUM levels (50M / 250M / 1B).

Design principles enforced here
-------------------------------
* Point-in-time: the only forward-looking object used is the *realised* next-overnight
  return ``r_on_next`` which is the trade outcome, never an input to position sizing.
* Dollar neutrality: long book dollars == short book dollars on every date.
* Participation cap: per-name dollar position is capped at 5% of ADV20 (Stage-2), with
  iterative pro-rata redistribution of unused dollars across the basket (Section 6.2).
* Costs: commission 0.5 bps/leg + auction slippage 1.5 bps/leg = 4.0 bps round-trip on
  traded notional, charged every day (overnight strategy fully turns over each session);
  borrow charged daily on short notional at the tier rate (A=40, B=200, C=800 bps p.a.).

All paths default to the coursework data layout. The 2024-12-31 cutoff is a single
configurable parameter so the held-out 2025-2026 window is never read during development.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# Fixed configuration (Section 6.3 cost schedule - these numbers are NOT chosen by us)
# --------------------------------------------------------------------------------------

TRADING_DAYS_PER_YEAR: int = 252


@dataclass(frozen=True)
class CostSchedule:
    """The fixed Section 6.3 cost schedule. Rates are in basis points."""

    commission_bps_per_leg: float = 0.5
    slippage_bps_per_leg: float = 1.5
    legs_per_round_trip: int = 2  # MOC entry on day t + MOO exit on day t+1

    @property
    def round_trip_bps(self) -> float:
        """Commission + slippage for one full round trip = 4.0 bps."""
        return (self.commission_bps_per_leg + self.slippage_bps_per_leg) * self.legs_per_round_trip

    @property
    def commission_round_trip_bps(self) -> float:
        return self.commission_bps_per_leg * self.legs_per_round_trip

    @property
    def slippage_round_trip_bps(self) -> float:
        return self.slippage_bps_per_leg * self.legs_per_round_trip


def _find_coursework_root() -> Path:
    """Locate the coursework root by walking up until the Stage-4 data is found.

    Works whether this Stage_5 folder sits directly at the coursework root or is nested
    one or more levels deep (e.g. inside a review/sharing wrapper). Falls back to the
    grandparent directory if the anchor is never found.
    """
    anchor = Path("Stage_4", "XGBoost2_prediction_outcome", "xgboost2_predictions_all.parquet")
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / anchor).exists():
            return parent
    return here.parents[1]


@dataclass
class Step5Config:
    """All choices the group makes for Step 5 (documented in the report)."""

    # Portfolio-AUM levels required by Section 6.5 (dollars).
    aum_levels: tuple[int, ...] = (50_000_000, 250_000_000, 1_000_000_000)
    # Basket selection: top / bottom quantile of the eligible cross-section.
    # 0.02 (top/bottom ~2%) was selected by net Sharpe on the VALIDATION split only
    # (see select_hyperparams / q1.py). A wider decile dilutes the spread below the
    # 4 bps/day round-trip cost, so the concentrated basket is required to clear costs.
    quantile: float = 0.02
    # Ensemble weight on the Ridge rank (XGBoost2 gets 1 - w_ridge). Selected on validation.
    w_ridge: float = 0.30
    # Development cutoff - nothing dated after this is read while designing the strategy.
    cutoff: str = "2024-12-31"
    # Random seed for any stochastic step (none currently, kept for reproducibility).
    seed: int = 20260531

    cost: CostSchedule = field(default_factory=CostSchedule)

    # Data locations - auto-discovered so the package runs nested or at the root.
    root: Path = field(default_factory=_find_coursework_root)

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)


# --------------------------------------------------------------------------------------
# Data loading and merging
# --------------------------------------------------------------------------------------

def load_panel(cfg: Step5Config) -> pd.DataFrame:
    """Merge the four Stage-2/3/4 artefacts into a single point-in-time trading panel.

    Returns one row per (date, instrument_id) eligible stock-day, carrying:
      * realised next-overnight return ``r_on_next`` (trade outcome),
      * the two model scores (``score_xgb_rank``, ``ridge_score``) and split label,
      * per-AUM participation caps ``max_pos_<aum>`` (= 5% of ADV20),
      * daily borrow cost ``borrow_daily_bps`` and ``borrow_tier``.
    """
    # --- Stage-4 XGBoost2 panel: realised returns + xgb rank score, full 2010-2024 window
    xgb = pd.read_parquet(
        cfg.path("Stage_4", "XGBoost2_prediction_outcome", "xgboost2_predictions_all.parquet"),
        columns=["date", "instrument_id", "ticker", "sample_split",
                 "is_trade_eligible", "target_r_on_next", "score_xgboost2_rank"],
    )
    xgb = xgb[xgb["is_trade_eligible"]].copy()
    xgb = xgb.rename(columns={"target_r_on_next": "r_on_next",
                              "score_xgboost2_rank": "score_xgb_rank"})

    # --- Stage-4 Ridge out-of-sample scores (validation 2019-21 + test 2022-24)
    ridge = pd.read_parquet(
        cfg.path("Stage_4", "Rridge_Regression_Predictions_output", "ridge_oos_predictions.parquet"),
        columns=["date", "instrument_id", "ridge_score"],
    )

    # --- Stage-2 capacity / eligibility: per-AUM participation caps (5% of ADV20)
    cap_cols = [f"max_position_by_adv_{a // 1_000_000}m" for a in cfg.aum_levels]
    elig = pd.read_parquet(
        cfg.path("stage2_outputs_from_stage1_2", "stage2_capacity_eligibility.parquet"),
        columns=["date", "instrument_id", "is_trade_eligible", "adv20", *cap_cols],
    )
    elig = elig[elig["is_trade_eligible"]].drop(columns="is_trade_eligible")
    rename_caps = {f"max_position_by_adv_{a // 1_000_000}m": f"max_pos_{a}" for a in cfg.aum_levels}
    elig = elig.rename(columns=rename_caps)

    # --- Stage-3 borrow tiers: daily borrow cost on the short leg
    borrow = pd.read_parquet(
        cfg.path("handoff_stage3_from_stage1_2", "step3_outputs", "step3_borrow_tiers.parquet"),
        columns=["date", "instrument_id", "borrow_tier", "borrow_cost_daily_bps", "dsi"],
    )
    borrow = borrow.rename(columns={"borrow_cost_daily_bps": "borrow_daily_bps"})

    panel = (xgb
             .merge(elig, on=["date", "instrument_id"], how="inner")
             .merge(borrow, on=["date", "instrument_id"], how="left")
             .merge(ridge, on=["date", "instrument_id"], how="left"))

    # Borrow defaults to Tier A (General Collateral, 40 bps p.a.) if a name is missing.
    tier_a_daily_bps = 40.0 / TRADING_DAYS_PER_YEAR
    panel["borrow_tier"] = panel["borrow_tier"].fillna("A")
    panel["borrow_daily_bps"] = panel["borrow_daily_bps"].fillna(tier_a_daily_bps)

    # Enforce the development cutoff (the held-out window is never read here).
    panel = panel[panel["date"] <= pd.Timestamp(cfg.cutoff)].copy()
    panel = panel.sort_values(["date", "instrument_id"]).reset_index(drop=True)
    return panel


# --------------------------------------------------------------------------------------
# Ensemble score
# --------------------------------------------------------------------------------------

def add_ensemble_score(panel: pd.DataFrame, w_ridge: float) -> pd.DataFrame:
    """Add a blended cross-sectional score = w_ridge*rank(ridge) + (1-w)*rank(xgb).

    Both models are mapped to a per-day uniform rank in (0, 1] before blending so the two
    very different score scales (Ridge predicted return vs XGBoost rank) combine fairly.
    Rows without a Ridge score (outside 2019-2024) get the XGBoost rank only.
    """
    df = panel.copy()
    df["rank_xgb"] = df.groupby("date")["score_xgb_rank"].rank(pct=True)
    df["rank_ridge"] = df.groupby("date")["ridge_score"].rank(pct=True)

    has_ridge = df["rank_ridge"].notna()
    df["score_ensemble"] = df["rank_xgb"]
    df.loc[has_ridge, "score_ensemble"] = (
        w_ridge * df.loc[has_ridge, "rank_ridge"]
        + (1.0 - w_ridge) * df.loc[has_ridge, "rank_xgb"]
    )
    return df


# --------------------------------------------------------------------------------------
# Participation-cap sizing (Section 6.2 iterative pro-rata redistribution)
# --------------------------------------------------------------------------------------

def water_fill(caps: np.ndarray, total: float, max_iter: int = 200) -> np.ndarray:
    """Spread ``total`` dollars equally across names, capped per-name at ``caps``.

    Implements the Section 6.2 rule: start from equal weights; any name over its cap is
    set to the cap and the freed dollars are redistributed pro-rata across names not yet
    at the cap; iterate until convergence or the basket is saturated (then it under-fills,
    and the caller reduces gross exposure accordingly).
    """
    caps = np.asarray(caps, dtype=float)
    n = caps.size
    if n == 0:
        return caps
    pos = np.minimum(caps, total / n)
    for _ in range(max_iter):
        deficit = total - pos.sum()
        if deficit <= total * 1e-12:
            break
        room = caps - pos
        free = room > 1e-9
        if not free.any():
            break  # basket saturated - cannot absorb full target
        pos[free] += np.minimum(deficit / free.sum(), room[free])
    return pos


# --------------------------------------------------------------------------------------
# Daily back-test for one AUM level
# --------------------------------------------------------------------------------------

def backtest(panel: pd.DataFrame, aum: int, cfg: Step5Config,
             score_col: str = "score_ensemble") -> pd.DataFrame:
    """Run the daily long/short overnight back-test at one portfolio-AUM level.

    Returns a per-date DataFrame with gross/net returns, the cost decomposition, basket
    sizes, realised gross exposure and turnover - everything needed for Section 6.5.
    """
    cap_col = f"max_pos_{aum}"
    cost = cfg.cost
    rows: list[dict] = []

    for date, day in panel.groupby("date", sort=True):
        day = day.dropna(subset=[score_col, "r_on_next", cap_col])
        if len(day) < 20:  # too thin to form two baskets
            continue

        n_side = max(1, int(round(len(day) * cfg.quantile)))
        ordered = day.sort_values(score_col)
        shorts = ordered.iloc[:n_side]
        longs = ordered.iloc[-n_side:]

        target_book = 0.5 * aum  # gross = 100% AUM => 50% per side
        long_pos = water_fill(longs[cap_col].to_numpy(), target_book)
        short_pos = water_fill(shorts[cap_col].to_numpy(), target_book)

        # Dollar neutrality: scale the larger book down so long$ == short$.
        long_book, short_book = long_pos.sum(), short_pos.sum()
        book = min(long_book, short_book)
        if book <= 0:
            continue
        long_pos *= book / long_book
        short_pos *= book / short_book

        long_ret = longs["r_on_next"].to_numpy()
        short_ret = shorts["r_on_next"].to_numpy()

        # Gross overnight P&L (long earns +r, short earns -r).
        pnl_gross = float(long_pos @ long_ret - short_pos @ short_ret)

        gross_notional = long_book and (long_pos.sum() + short_pos.sum())  # = 2*book
        # Round-trip commission + slippage on all traded notional, every day.
        commission = cost.commission_round_trip_bps / 1e4 * gross_notional
        slippage = cost.slippage_round_trip_bps / 1e4 * gross_notional
        # Daily borrow on the short notional at each name's tier rate.
        borrow = float(short_pos @ (shorts["borrow_daily_bps"].to_numpy() / 1e4))

        pnl_net = pnl_gross - commission - slippage - borrow

        rows.append({
            "date": date,
            "n_long": len(longs), "n_short": len(shorts),
            "gross_exposure": gross_notional / aum,
            "ret_gross": pnl_gross / aum,
            "ret_net": pnl_net / aum,
            "cost_commission": commission / aum,
            "cost_slippage": slippage / aum,
            "cost_borrow": borrow / aum,
            "turnover": gross_notional / aum,  # one-way notional traded / AUM
            "max_pos": float(max(long_pos.max(), short_pos.max())),
            "mean_pos": float(np.concatenate([long_pos, short_pos]).mean()),
        })

    out = pd.DataFrame(rows).set_index("date")
    out.attrs["aum"] = aum
    return out


# --------------------------------------------------------------------------------------
# Performance metrics
# --------------------------------------------------------------------------------------

def _ann_sharpe(r: pd.Series) -> float:
    sd = r.std(ddof=1)
    return float(np.sqrt(TRADING_DAYS_PER_YEAR) * r.mean() / sd) if sd > 0 else np.nan


def _max_drawdown(r: pd.Series) -> float:
    curve = (1.0 + r).cumprod()
    return float((curve / curve.cummax() - 1.0).min())


def performance_metrics(daily: pd.DataFrame, aum: int) -> dict:
    """Compute the Section 6.5 headline metrics from a back-test daily frame."""
    rn = daily["ret_net"]
    rg = daily["ret_gross"]
    gross_cap = 0.999  # 'at cap' = realised gross exposure below ~100% because caps bound
    return {
        "aum": aum,
        "n_days": int(len(daily)),
        "net_ann_return": float(rn.mean() * TRADING_DAYS_PER_YEAR),
        "net_ann_vol": float(rn.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)),
        "net_sharpe": _ann_sharpe(rn),
        "gross_sharpe": _ann_sharpe(rg),
        "max_drawdown": _max_drawdown(rn),
        "avg_daily_turnover": float(daily["turnover"].mean()),
        "avg_gross_exposure": float(daily["gross_exposure"].mean()),
        "frac_days_at_cap": float((daily["gross_exposure"] < gross_cap).mean()),
        "borrow_sharpe_drag": _ann_sharpe(rg) - _ann_sharpe(rg - daily["cost_borrow"]),
    }


def cost_decomposition(daily: pd.DataFrame) -> pd.DataFrame:
    """Gross-to-net Sharpe degradation, attributed to commission / slippage / borrow."""
    stages = {
        "gross": daily["ret_gross"],
        "- commission": daily["ret_gross"] - daily["cost_commission"],
        "- slippage": daily["ret_gross"] - daily["cost_commission"] - daily["cost_slippage"],
        "- borrow (net)": daily["ret_net"],
    }
    sh = {k: _ann_sharpe(v) for k, v in stages.items()}
    return pd.DataFrame({
        "sharpe": sh,
        "sharpe_drop": {k: (None if i == 0 else list(sh.values())[i - 1] - v)
                        for i, (k, v) in enumerate(sh.items())},
    })


# --------------------------------------------------------------------------------------
# Benchmark + QuantStats tear-sheet (Section 6.5 deliverable)
# --------------------------------------------------------------------------------------

def load_benchmark(cfg: Step5Config) -> pd.Series:
    """Daily total-return series of SP500_TR, aligned to a return series later."""
    bench = pd.read_parquet(cfg.path("sp500_tr.parquet"), columns=["date", "adjusted_close"])
    bench = bench[bench["date"] <= pd.Timestamp(cfg.cutoff)].set_index("date")["adjusted_close"]
    return bench.pct_change().dropna()


def make_tearsheet(net_returns: pd.Series, benchmark: pd.Series, out_html: Path,
                   title: str = "C2O Overnight L/S - 250M AUM") -> None:
    """Render the QuantStats HTML tear-sheet vs SP500_TR (Section 6.5)."""
    import quantstats as qs

    r = net_returns.copy()
    r.index = pd.to_datetime(r.index)
    b = benchmark.reindex(r.index).fillna(0.0)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    qs.reports.html(r, benchmark=b, output=str(out_html), title=title)


# --------------------------------------------------------------------------------------
# Shared pipeline helpers (used by every q*.py entry script)
# --------------------------------------------------------------------------------------

# Back-test windows (split labels). ``full_2010_2024`` satisfies the brief's
# development-window request, but its 2010-2018 portion is in-sample for XGBoost.
# ``oos_2019_2024`` is the honest out-of-sample window common to both models.
WINDOWS: dict[str, list[str]] = {
    "full_2010_2024": ["train", "valid", "test"],
    "validation_2019_2021": ["valid"],
    "test_2022_2024": ["test"],
    "oos_2019_2024": ["valid", "test"],
}


def add_xgb_score(panel: pd.DataFrame) -> pd.DataFrame:
    """Add the XGBoost-only cross-sectional score for full-window headline reporting."""
    df = panel.copy()
    df["score_xgb"] = df.groupby("date")["score_xgb_rank"].rank(pct=True)
    return df


def run_window(panel: pd.DataFrame, cfg: Step5Config, splits: list[str],
               aum: int, model: str = "ensemble") -> pd.DataFrame:
    """Back-test one window x AUM.

    ``model="xgb"`` uses the XGBoost-only score, which has full 2010-2024 coverage.
    ``model="ensemble"`` uses the Ridge+XGBoost blend and is meaningful on 2019-2024,
    where the Ridge OOS score is available.
    """
    sub = panel[panel["sample_split"].isin(splits)].copy()
    if model == "xgb":
        scored = add_xgb_score(sub)
        return backtest(scored, aum, cfg, score_col="score_xgb")
    if model != "ensemble":
        raise ValueError(f"Unknown model: {model}")
    scored = add_ensemble_score(sub, cfg.w_ridge)
    return backtest(scored, aum, cfg, score_col="score_ensemble")


# NOTE: the Q1 helper (select_hyperparams) lives in q1.py and the Q2 helper
# (headline_table) lives in q2.py - each question owns its own analysis logic.


def stress_windows(daily: pd.DataFrame) -> pd.DataFrame:
    """Behaviour in named dislocations from one daily frame (Q5 / Section 7.2)."""
    defs = {
        "2020Q1_covid": ("2020-01-01", "2020-03-31"),
        "2022_drawdown": ("2022-01-01", "2022-12-31"),
        "2023_recovery": ("2023-01-01", "2023-12-31"),
        "full_window": (str(daily.index.min().date()), str(daily.index.max().date())),
    }
    rows = []
    for name, (a, b) in defs.items():
        w = daily.loc[a:b]
        if len(w) < 5:
            continue
        rows.append({"window": name, "n_days": len(w),
                     "net_sharpe": _ann_sharpe(w["ret_net"]),
                     "net_cum_return": float((1 + w["ret_net"]).prod() - 1),
                     "max_drawdown": _max_drawdown(w["ret_net"]),
                     "worst_day": float(w["ret_net"].min())})
    return pd.DataFrame(rows)
