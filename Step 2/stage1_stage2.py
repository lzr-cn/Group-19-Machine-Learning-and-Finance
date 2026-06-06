"""Stage 1 and Stage 2 pipeline for the C2O coursework.

The script builds:
1. A point-in-time daily price/return panel and the frozen yearly top-1000
   base universe.
2. Clean earnings and short-interest timing tables.
3. A capacity-aware eligibility table for Step 2 of the brief.

Run from the repository root:
    python src/stage1_stage2.py
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "stage_outputs"


@dataclass(frozen=True)
class Config:
    development_start: str = "2010-01-01"
    development_end: str = "2024-12-31"
    return_reconciliation_tolerance: float = 1e-8
    min_price: float = 5.0
    min_adv20: float = 10_000_000.0
    min_ann_vol: float = 0.05
    max_ann_vol: float = 1.50
    adv_window: int = 20
    volatility_window: int = 60
    volatility_min_periods: int = 40
    earnings_window_trading_days: int = 1
    participation_cap: float = 0.05
    impact_k: float = 0.70
    basket_names_per_side: int = 100
    portfolio_aums: tuple[int, ...] = (50_000_000, 250_000_000, 1_000_000_000)


CFG = Config()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _calendar_helpers(dates: pd.Series) -> tuple[pd.DatetimeIndex, dict, dict]:
    calendar = pd.DatetimeIndex(pd.Series(dates).dropna().drop_duplicates().sort_values())
    next_map = dict(zip(calendar[:-1], calendar[1:]))
    prev_map = dict(zip(calendar[1:], calendar[:-1]))
    return calendar, next_map, prev_map


def _next_trading_on_or_after(values: pd.Series, calendar: pd.DatetimeIndex) -> pd.Series:
    idx = np.searchsorted(calendar.values, values.values.astype("datetime64[ns]"), side="left")
    out = np.full(len(values), np.datetime64("NaT"), dtype="datetime64[ns]")
    valid = idx < len(calendar)
    out[valid] = calendar.values[idx[valid]]
    return pd.Series(out, index=values.index)


def _next_trading_after(values: pd.Series, calendar: pd.DatetimeIndex) -> pd.Series:
    idx = np.searchsorted(calendar.values, values.values.astype("datetime64[ns]"), side="right")
    out = np.full(len(values), np.datetime64("NaT"), dtype="datetime64[ns]")
    valid = idx < len(calendar)
    out[valid] = calendar.values[idx[valid]]
    return pd.Series(out, index=values.index)


def _previous_trading_before(values: pd.Series, calendar: pd.DatetimeIndex) -> pd.Series:
    idx = np.searchsorted(calendar.values, values.values.astype("datetime64[ns]"), side="left") - 1
    out = np.full(len(values), np.datetime64("NaT"), dtype="datetime64[ns]")
    valid = idx >= 0
    out[valid] = calendar.values[idx[valid]]
    return pd.Series(out, index=values.index)


def build_price_panel() -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    raw = pd.read_parquet(ROOT / "prices.parquet", engine="pyarrow")
    raw["date"] = pd.to_datetime(raw["date"])
    raw = raw.sort_values(["instrument_id", "date", "updated"])

    duplicate_rows = int(raw.duplicated(["instrument_id", "date"]).sum())
    prices = raw.drop_duplicates(["instrument_id", "date"], keep="last").copy()
    prices = prices[prices["date"] <= pd.Timestamp(CFG.development_end)].copy()

    valid_factor = (
        prices["close"].gt(0)
        & prices["adjusted_close"].gt(0)
        & prices["open"].gt(0)
        & prices["volume"].ge(0)
    )
    prices["adj_factor"] = np.where(
        valid_factor, prices["adjusted_close"] / prices["close"], np.nan
    )
    prices["Open_t"] = prices["open"] * prices["adj_factor"]
    prices["High_t"] = prices["high"] * prices["adj_factor"]
    prices["Low_t"] = prices["low"] * prices["adj_factor"]
    prices["Close_t"] = prices["adjusted_close"]
    prices["Volume_t"] = prices["volume"] / prices["adj_factor"]
    prices["DollarVolume_t"] = prices["Close_t"] * prices["Volume_t"]

    prices = prices.sort_values(["instrument_id", "date"])
    by_stock = prices.groupby("instrument_id", sort=False)
    prices["Close_lag1"] = by_stock["Close_t"].shift(1)
    prices["r_on"] = prices["Open_t"] / prices["Close_lag1"] - 1.0
    prices["r_id"] = prices["Close_t"] / prices["Open_t"] - 1.0
    prices["r_cc"] = prices["Close_t"] / prices["Close_lag1"] - 1.0
    prices["recon_lhs"] = (1.0 + prices["r_on"]) * (1.0 + prices["r_id"]) - 1.0
    prices["recon_error"] = prices["recon_lhs"] - prices["r_cc"]
    prices["abs_recon_error"] = prices["recon_error"].abs()

    calendar, _, _ = _calendar_helpers(prices["date"])
    audit = pd.DataFrame(
        [
            {
                "metric": "raw_rows",
                "value": len(raw),
            },
            {
                "metric": "duplicate_instrument_date_rows",
                "value": duplicate_rows,
            },
            {
                "metric": "panel_rows_after_dedup",
                "value": len(prices),
            },
            {
                "metric": "invalid_adjustment_factor_rows",
                "value": int(prices["adj_factor"].isna().sum()),
            },
            {
                "metric": "max_abs_return_reconciliation_error",
                "value": float(prices["abs_recon_error"].max(skipna=True)),
            },
            {
                "metric": "reconciliation_fail_count",
                "value": int(
                    prices["abs_recon_error"].gt(
                        CFG.return_reconciliation_tolerance
                    ).sum()
                ),
            },
            {
                "metric": "reconciliation_fail_fraction",
                "value": float(
                    prices["abs_recon_error"]
                    .gt(CFG.return_reconciliation_tolerance)
                    .mean()
                ),
            },
        ]
    )

    return prices, audit, calendar


def build_earnings_tables(calendar: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    earnings = pd.read_parquet(ROOT / "earnings_calendar.parquet", engine="pyarrow")
    earnings["reporting_date"] = pd.to_datetime(earnings["reporting_date"])
    earnings["period_end_date"] = pd.to_datetime(earnings["period_end_date"])

    event_ts_utc = earnings["reporting_date"] + earnings["reporting_time"]
    event_ts_et = event_ts_utc.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    decision_cutoff_et = (
        pd.to_datetime(earnings["reporting_date"].dt.strftime("%Y-%m-%d") + " 15:50:00")
        .dt.tz_localize("America/New_York")
    )

    earnings["report_timestamp_et"] = event_ts_et.astype(str)
    earnings["decision_cutoff_et"] = decision_cutoff_et.astype(str)
    earnings["reporting_trading_date"] = _next_trading_on_or_after(
        earnings["reporting_date"], calendar
    )
    next_after_report = _next_trading_after(earnings["reporting_date"], calendar)
    prev_before_report = _previous_trading_before(earnings["reporting_date"], calendar)

    flag = earnings["before_after_market"].fillna("same_day").str.lower()
    available = earnings["reporting_trading_date"].copy()
    available.loc[flag.eq("after")] = next_after_report.loc[flag.eq("after")]

    same_day = flag.eq("same_day") | flag.eq("none")
    same_day_after_cutoff = same_day & (event_ts_et > decision_cutoff_et)
    available.loc[same_day_after_cutoff] = next_after_report.loc[same_day_after_cutoff]

    earnings["available_date"] = available
    earnings["event_exposure_close_date"] = earnings["reporting_trading_date"]
    earnings.loc[flag.eq("before"), "event_exposure_close_date"] = prev_before_report.loc[
        flag.eq("before")
    ]

    rows: list[tuple[int, pd.Timestamp]] = []
    for stock_id, center in earnings[["stock_id", "reporting_trading_date"]].itertuples(
        index=False
    ):
        if pd.isna(center):
            continue
        center_idx = calendar.searchsorted(center)
        start_idx = max(0, center_idx - CFG.earnings_window_trading_days)
        end_idx = min(len(calendar) - 1, center_idx + CFG.earnings_window_trading_days)
        for date in calendar[start_idx : end_idx + 1]:
            rows.append((int(stock_id), pd.Timestamp(date)))

    earnings_window = pd.DataFrame(rows, columns=["instrument_id", "date"]).drop_duplicates()
    earnings_window["earnings_window"] = True

    cols = [
        "stock_id",
        "reporting_date",
        "reporting_trading_date",
        "strat_trading_date",
        "reporting_time",
        "report_timestamp_et",
        "before_after_market",
        "period",
        "period_end_date",
        "available_date",
        "event_exposure_close_date",
    ]
    return earnings[cols].rename(columns={"stock_id": "instrument_id"}), earnings_window


def build_short_interest_daily(calendar: pd.DatetimeIndex) -> pd.DataFrame:
    short_interest = pd.read_parquet(ROOT / "short_interest_transfo.parquet", engine="pyarrow")
    short_interest = short_interest.rename(columns={"stock_id": "instrument_id"})
    short_interest["date"] = pd.to_datetime(short_interest["date"])
    short_interest = short_interest.sort_values(["instrument_id", "date"])

    dev_calendar = calendar[
        (calendar >= pd.Timestamp(CFG.development_start))
        & (calendar <= pd.Timestamp(CFG.development_end))
    ]
    prev_dates = pd.Series(dev_calendar, name="date").map(dict(zip(calendar[1:], calendar[:-1])))
    base_dates = pd.DataFrame({"date": dev_calendar, "feature_asof_date": prev_dates.values})

    frames: list[pd.DataFrame] = []
    for instrument_id, group in short_interest.groupby("instrument_id", sort=False):
        group = group[["date", "dsi", "dtcn", "ddtcn"]].dropna(subset=["date"]).copy()
        merged = pd.merge_asof(
            base_dates.sort_values("feature_asof_date"),
            group.rename(columns={"date": "short_interest_source_date"}).sort_values(
                "short_interest_source_date"
            ),
            left_on="feature_asof_date",
            right_on="short_interest_source_date",
            direction="backward",
        )
        merged["instrument_id"] = instrument_id
        frames.append(merged)

    daily = pd.concat(frames, ignore_index=True)
    daily = daily[
        [
            "instrument_id",
            "date",
            "feature_asof_date",
            "short_interest_source_date",
            "dsi",
            "dtcn",
            "ddtcn",
        ]
    ]
    return daily.dropna(subset=["dsi", "dtcn", "ddtcn"]).reset_index(drop=True)


def build_yearly_universe(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = prices.copy()
    prices["year"] = prices["date"].dt.year
    first_obs = prices.groupby("instrument_id", as_index=False)["date"].min()
    first_obs = first_obs.rename(columns={"date": "first_price_date"})

    year_ends = prices.groupby("year", as_index=False)["date"].max()
    year_ends = year_ends.rename(columns={"date": "rank_date"})
    year_ends["universe_year"] = year_ends["year"] + 1
    year_ends = year_ends[
        (year_ends["universe_year"] >= pd.Timestamp(CFG.development_start).year)
        & (year_ends["universe_year"] <= pd.Timestamp(CFG.development_end).year)
    ]

    rank_rows = prices.merge(year_ends[["rank_date", "universe_year"]], left_on="date", right_on="rank_date")
    rank_rows = rank_rows.merge(first_obs, on="instrument_id", how="left")
    rank_rows["has_12m_history"] = rank_rows["first_price_date"] <= (
        rank_rows["rank_date"] - pd.DateOffset(years=1)
    )
    rank_rows = rank_rows[
        rank_rows["has_12m_history"]
        & rank_rows["market_cap"].notna()
        & rank_rows["market_cap"].gt(0)
    ].copy()
    rank_rows["market_cap_rank"] = rank_rows.groupby("universe_year")["market_cap"].rank(
        method="first", ascending=False
    )

    universe = rank_rows[rank_rows["market_cap_rank"].le(1000)].copy()
    universe = universe[
        [
            "universe_year",
            "rank_date",
            "instrument_id",
            "ticker",
            "market_cap",
            "market_cap_rank",
            "first_price_date",
        ]
    ].rename(columns={"market_cap": "year_start_market_cap"})

    year_last = (
        prices.groupby("year", as_index=False)["date"].max().rename(columns={"date": "year_last_date"})
    )
    stock_year_last = (
        prices.groupby(["instrument_id", "year"], as_index=False)["date"]
        .max()
        .rename(columns={"date": "stock_last_date_in_year"})
    )
    exits = universe[["universe_year", "instrument_id"]].merge(
        stock_year_last,
        left_on=["universe_year", "instrument_id"],
        right_on=["year", "instrument_id"],
        how="left",
    ).merge(year_last, on="year", how="left")
    exits["mid_year_exit"] = exits["stock_last_date_in_year"] < exits["year_last_date"]
    audit = (
        exits.groupby("universe_year", as_index=False)
        .agg(
            eligible_names_at_year_start=("instrument_id", "nunique"),
            mid_year_exits=("mid_year_exit", "sum"),
        )
        .sort_values("universe_year")
    )

    return universe.sort_values(["universe_year", "market_cap_rank"]), audit


def attach_universe(prices: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    panel = prices.copy()
    panel["year"] = panel["date"].dt.year
    panel = panel.merge(
        universe[
            [
                "universe_year",
                "instrument_id",
                "year_start_market_cap",
                "market_cap_rank",
            ]
        ],
        left_on=["year", "instrument_id"],
        right_on=["universe_year", "instrument_id"],
        how="left",
    )
    panel["in_base_universe"] = panel["universe_year"].notna()
    return panel.drop(columns=["universe_year"])


def make_sanity_plot(panel: pd.DataFrame) -> pd.DataFrame:
    dev = panel[
        panel["date"].between(CFG.development_start, CFG.development_end)
        & panel["in_base_universe"]
        & panel["r_on"].notna()
        & panel["r_id"].notna()
        & panel["r_cc"].notna()
    ].copy()

    daily = (
        dev.groupby("date", as_index=False)
        .agg(
            ew_r_on=("r_on", "mean"),
            ew_r_id=("r_id", "mean"),
            ew_r_cc=("r_cc", "mean"),
            n_names=("instrument_id", "nunique"),
        )
        .sort_values("date")
    )
    daily["growth_on"] = (1.0 + daily["ew_r_on"]).cumprod()
    daily["growth_id"] = (1.0 + daily["ew_r_id"]).cumprod()
    daily["growth_cc"] = (1.0 + daily["ew_r_cc"]).cumprod()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(daily["date"], daily["growth_on"], label="Overnight")
    ax.plot(daily["date"], daily["growth_id"], label="Intraday")
    ax.plot(daily["date"], daily["growth_cc"], label="Close-to-close")
    ax.set_title("Equally weighted base universe: growth of $1")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative growth")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "stage1_equal_weight_sanity.png", dpi=160)
    plt.close(fig)
    return daily


def build_stage2_eligibility(
    panel: pd.DataFrame, earnings_window: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dev = panel[
        panel["date"].between(CFG.development_start, CFG.development_end)
        & panel["in_base_universe"]
    ].copy()
    dev = dev.sort_values(["instrument_id", "date"])

    by_stock = dev.groupby("instrument_id", sort=False)
    dev["price_for_filter"] = by_stock["Close_t"].shift(1)
    dev["adv20"] = by_stock["DollarVolume_t"].transform(
        lambda s: s.shift(1).rolling(CFG.adv_window, min_periods=CFG.adv_window).mean()
    )
    dev["daily_vol60"] = by_stock["r_cc"].transform(
        lambda s: s.shift(1)
        .rolling(CFG.volatility_window, min_periods=CFG.volatility_min_periods)
        .std()
    )
    dev["ann_vol60"] = dev["daily_vol60"] * np.sqrt(252.0)

    dev = dev.merge(earnings_window, on=["instrument_id", "date"], how="left")
    dev["earnings_window"] = dev["earnings_window"].fillna(False)

    missing = dev[["price_for_filter", "adv20", "ann_vol60"]].isna().any(axis=1)
    reason = pd.Series("OK", index=dev.index, dtype="object")
    reason.loc[missing] = "MISSING_LOOKBACK"
    reason.loc[~missing & dev["price_for_filter"].lt(CFG.min_price)] = "PRICE_FAIL"
    reason.loc[~missing & reason.eq("OK") & dev["adv20"].lt(CFG.min_adv20)] = "ADV_FAIL"
    reason.loc[
        ~missing
        & reason.eq("OK")
        & (dev["ann_vol60"].lt(CFG.min_ann_vol) | dev["ann_vol60"].gt(CFG.max_ann_vol))
    ] = "VOL_FAIL"
    reason.loc[reason.eq("OK") & dev["earnings_window"]] = "EARN_WINDOW"
    dev["eligibility_reason"] = reason
    dev["is_trade_eligible"] = dev["eligibility_reason"].eq("OK")

    dev["impact_bps_at_participation_cap"] = (
        CFG.impact_k
        * dev["daily_vol60"]
        * np.sqrt(CFG.participation_cap)
        * 10_000.0
    )

    for aum in CFG.portfolio_aums:
        suffix = f"{aum // 1_000_000}m"
        target = aum / (2.0 * CFG.basket_names_per_side)
        max_by_adv = CFG.participation_cap * dev["adv20"]
        dev[f"target_position_{suffix}"] = target
        dev[f"max_position_by_adv_{suffix}"] = max_by_adv
        dev[f"position_limit_{suffix}"] = np.minimum(target, max_by_adv)
        dev[f"binding_constraint_{suffix}"] = np.where(
            max_by_adv < target, "PARTICIPATION_CAP", "TARGET_WEIGHT"
        )
        dev.loc[~dev["is_trade_eligible"], f"binding_constraint_{suffix}"] = dev.loc[
            ~dev["is_trade_eligible"], "eligibility_reason"
        ]

    keep_cols = [
        "date",
        "year",
        "ticker",
        "instrument_id",
        "market_cap_rank",
        "year_start_market_cap",
        "price_for_filter",
        "adv20",
        "ann_vol60",
        "earnings_window",
        "eligibility_reason",
        "is_trade_eligible",
        "impact_bps_at_participation_cap",
    ]
    for aum in CFG.portfolio_aums:
        suffix = f"{aum // 1_000_000}m"
        keep_cols += [
            f"target_position_{suffix}",
            f"max_position_by_adv_{suffix}",
            f"position_limit_{suffix}",
            f"binding_constraint_{suffix}",
        ]

    eligibility = dev[keep_cols].copy()

    reason_summary = (
        eligibility.groupby(["year", "eligibility_reason"], as_index=False)
        .agg(stock_days=("instrument_id", "size"), names=("instrument_id", "nunique"))
        .sort_values(["year", "eligibility_reason"])
    )

    yearly = (
        eligibility.groupby("date", as_index=False)
        .agg(
            base_names=("instrument_id", "nunique"),
            eligible_names=("is_trade_eligible", "sum"),
        )
    )
    yearly["year"] = yearly["date"].dt.year
    yearly_summary = (
        yearly.groupby("year", as_index=False)
        .agg(
            avg_base_names=("base_names", "mean"),
            avg_eligible_names=("eligible_names", "mean"),
            min_eligible_names=("eligible_names", "min"),
            max_eligible_names=("eligible_names", "max"),
        )
        .sort_values("year")
    )

    binding_frames = []
    for aum in CFG.portfolio_aums:
        suffix = f"{aum // 1_000_000}m"
        tmp = (
            eligibility.groupby(["year", f"binding_constraint_{suffix}"], as_index=False)
            .size()
            .rename(columns={"size": "stock_days", f"binding_constraint_{suffix}": "binding_constraint"})
        )
        tmp["aum"] = aum
        binding_frames.append(tmp)
    binding_summary = pd.concat(binding_frames, ignore_index=True)

    eligible = eligibility[eligibility["is_trade_eligible"]].copy()
    eligible["mcap_bucket"] = np.where(
        eligible["market_cap_rank"].le(500), "large_rank_1_500", "rank_501_1000"
    )
    slippage_summary = (
        eligible.groupby(["year", "mcap_bucket"], as_index=False)
        .agg(
            median_impact_bps=("impact_bps_at_participation_cap", "median"),
            p75_impact_bps=("impact_bps_at_participation_cap", lambda s: s.quantile(0.75)),
            median_adv20=("adv20", "median"),
            median_ann_vol60=("ann_vol60", "median"),
        )
        .sort_values(["year", "mcap_bucket"])
    )

    return eligibility, reason_summary, yearly_summary, binding_summary, slippage_summary


def main() -> None:
    OUT.mkdir(exist_ok=True)
    _write_json(OUT / "stage_parameters.json", asdict(CFG))

    prices, price_audit, calendar = build_price_panel()
    earnings, earnings_window = build_earnings_tables(calendar)
    short_interest_daily = build_short_interest_daily(calendar)
    universe, universe_audit = build_yearly_universe(prices)
    panel = attach_universe(prices, universe)
    sanity = make_sanity_plot(panel)

    stage1_panel_cols = [
        "ticker",
        "instrument_id",
        "date",
        "year",
        "status",
        "market_cap",
        "year_start_market_cap",
        "market_cap_rank",
        "in_base_universe",
        "Open_t",
        "High_t",
        "Low_t",
        "Close_t",
        "Volume_t",
        "DollarVolume_t",
        "adj_factor",
        "r_on",
        "r_id",
        "r_cc",
        "recon_error",
        "abs_recon_error",
    ]
    panel[stage1_panel_cols].to_parquet(OUT / "stage1_daily_panel.parquet", index=False)
    earnings.to_parquet(OUT / "stage1_earnings_events.parquet", index=False)
    earnings_window.to_parquet(OUT / "stage1_earnings_window_flags.parquet", index=False)
    short_interest_daily.to_parquet(OUT / "stage1_short_interest_daily.parquet", index=False)
    universe.to_csv(OUT / "stage1_yearly_universe.csv", index=False)
    price_audit.to_csv(OUT / "stage1_price_return_audit.csv", index=False)
    universe_audit.to_csv(OUT / "stage1_universe_audit.csv", index=False)
    sanity.to_csv(OUT / "stage1_equal_weight_sanity.csv", index=False)

    eligibility, reason_summary, yearly_summary, binding_summary, slippage_summary = (
        build_stage2_eligibility(panel, earnings_window)
    )
    eligibility.to_parquet(OUT / "stage2_capacity_eligibility.parquet", index=False)
    reason_summary.to_csv(OUT / "stage2_reason_summary.csv", index=False)
    yearly_summary.to_csv(OUT / "stage2_yearly_summary.csv", index=False)
    binding_summary.to_csv(OUT / "stage2_binding_summary.csv", index=False)
    slippage_summary.to_csv(OUT / "stage2_slippage_summary.csv", index=False)

    print("Stage 1/2 pipeline complete.")
    print(f"Outputs written to: {OUT}")
    print(price_audit.to_string(index=False))
    print(universe_audit.tail().to_string(index=False))
    print(yearly_summary.tail().to_string(index=False))


if __name__ == "__main__":
    main()
