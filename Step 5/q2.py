"""Section 6 · Q2 - headline performance table at 50M / 250M / 1B AUM.

Headline model = XGBoost-only score, because it is the only score with full 2010-2024
coverage (the Ridge leg of the ensemble exists only for 2019-2024). The full-window rows
include 2010-2018, which is the models' IN-SAMPLE training period - flagged explicitly in
the `contains_insample` column and to be disclosed in the report. The Ridge+XGB ensemble
is reported separately, only on the honest out-of-sample window, as a robustness check.
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd

import stage5_portfolio as s5

OUT = Path(__file__).resolve().parent / "Stage_5_portfolio_outputs"
OUT.mkdir(parents=True, exist_ok=True)

# headline_table's cache, keyed by (window, aum). NB: run_stage5's Section-7 diagnostic
# store is a different object keyed by (window, model, aum) - see run_stage5.DiagStore.
HeadlineStore = dict[tuple[str, int], pd.DataFrame]

SHOW = ["model", "contains_insample", "basket_quantile", "cost_round_trip_bps",
        "n_days", "net_ann_return", "net_ann_vol",
        "net_sharpe", "gross_sharpe", "max_drawdown", "avg_daily_turnover",
        "avg_gross_exposure", "frac_days_at_cap", "borrow_sharpe_drag"]

# Headline windows. full_2010_2024 satisfies the brief's literal "2010-2024" request but
# its 2010-2018 portion is in-sample; the OOS windows are the honest numbers.
HEADLINE_WINDOWS: dict[str, list[str]] = {
    "full_2010_2024": ["train", "valid", "test"],
    "oos_2019_2024": ["valid", "test"],
    "test_2022_2024": ["test"],
}


def headline_table(panel: pd.DataFrame, cfg: s5.Step5Config) -> tuple[pd.DataFrame, HeadlineStore]:
    """Section 6.5 headline (XGBoost-only) at all three AUM levels, per window (Q2).

    Returns the table plus ``store`` (per-date frames keyed by (window, aum)).
    """
    records, store = [], {}
    for wname, splits in HEADLINE_WINDOWS.items():
        for aum in cfg.aum_levels:
            daily = s5.run_window(panel, cfg, splits, aum, model="xgb")
            store[(wname, aum)] = daily
            m = s5.performance_metrics(daily, aum)
            m["window"] = wname
            m["model"] = "xgboost_only"
            m["contains_insample"] = "train" in splits  # 2010-2018 is in-sample
            m["basket_quantile"] = cfg.quantile
            m["cost_round_trip_bps"] = cfg.cost.round_trip_bps
            records.append(m)
    table = pd.DataFrame(records).set_index(["window", "aum"])
    return table, store


def ensemble_robustness(panel: pd.DataFrame, cfg: s5.Step5Config) -> pd.DataFrame:
    """Robustness: Ridge+XGB ensemble vs XGBoost-only, on the OOS windows only."""
    windows = {"oos_2019_2024": ["valid", "test"], "test_2022_2024": ["test"]}
    records = []
    for wname, splits in windows.items():
        for aum in cfg.aum_levels:
            for model in ("ensemble", "xgb"):
                daily = s5.run_window(panel, cfg, splits, aum, model=model)
                m = s5.performance_metrics(daily, aum)
                m["window"] = wname
                m["model"] = "ridge_xgb_ensemble" if model == "ensemble" else "xgboost_only"
                m["basket_quantile"] = cfg.quantile
                m["cost_round_trip_bps"] = cfg.cost.round_trip_bps
                records.append(m)
    return pd.DataFrame(records).set_index(["window", "aum", "model"])


def main() -> None:
    cfg = s5.Step5Config()
    panel = s5.load_panel(cfg)

    table, _ = headline_table(panel, cfg)
    table.to_csv(OUT / "stage5_headline_performance.csv")
    robust = ensemble_robustness(panel, cfg)
    robust.to_csv(OUT / "stage5_ensemble_robustness.csv")

    print(f"Config: quantile={cfg.quantile}, w_ridge={cfg.w_ridge} (ensemble only), "
          f"cost round-trip={cfg.cost.round_trip_bps} bps")
    print("\n=== Q2 headline (XGBoost-only) ===")
    print(table[SHOW].round(3).to_string())
    print("\n=== Ensemble robustness (OOS only) net Sharpe ===")
    print(robust["net_sharpe"].unstack("model").round(2).to_string())


if __name__ == "__main__":
    main()
