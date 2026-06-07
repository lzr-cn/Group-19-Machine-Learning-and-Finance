"""Stage 5 - single-command reproduction.

This script keeps two reporting layers separate:
* headline: XGBoost-only, full 2010-2024, because it has full development-window coverage;
* robustness: Ridge+XGBoost ensemble, OOS 2019-2024, because Ridge exists only OOS.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import numpy as np
import pandas as pd

import stage5_portfolio as s5
from q1 import basket_turnover_table, select_hyperparams
from q2 import ensemble_robustness, headline_table

OUT = Path(__file__).resolve().parent / "Stage_5_portfolio_outputs"
OUT.mkdir(parents=True, exist_ok=True)

DiagStore = dict[tuple[str, str, int], pd.DataFrame]


def capacity_diagnostics(store: DiagStore, cfg: s5.Step5Config) -> pd.DataFrame:
    """Section 7.3 - per-stock position honesty across AUM levels."""
    rows = []
    for model in ("xgboost_only", "ridge_xgb_ensemble"):
        for aum in cfg.aum_levels:
            daily = store[("oos_2019_2024", model, aum)]
            rows.append({
                "window": "oos_2019_2024",
                "model": model,
                "aum": aum,
                "avg_per_stock_position": daily["mean_pos"].mean(),
                "peak_per_stock_position": daily["max_pos"].max(),
                "avg_gross_exposure": daily["gross_exposure"].mean(),
                "frac_days_caps_bind": float((daily["gross_exposure"] < 0.999).mean()),
            })
    return pd.DataFrame(rows)


def _borrow_honesty_one(scored: pd.DataFrame, score_col: str, cfg: s5.Step5Config,
                        si_threshold: float) -> dict:
    cap_col = "max_pos_250000000"
    contrib_high, contrib_total = 0.0, 0.0
    for _, day in scored.groupby("date"):
        day = day.dropna(subset=[score_col, "r_on_next", cap_col])
        if len(day) < 20:
            continue
        n = max(1, int(round(len(day) * cfg.quantile)))
        shorts = day.sort_values(score_col).iloc[:n]
        pnl = -shorts["r_on_next"].to_numpy()
        is_high = shorts["dsi"].fillna(0).to_numpy() > si_threshold
        contrib_high += float(pnl[is_high].sum())
        contrib_total += float(pnl.sum())
    return {
        "short_leg_gross_units_total": contrib_total,
        "short_leg_gross_units_high_si": contrib_high,
        "high_si_share_of_short_pnl": contrib_high / contrib_total if contrib_total else np.nan,
    }


def borrow_honesty(panel: pd.DataFrame, cfg: s5.Step5Config,
                   si_threshold: float = 0.10) -> pd.DataFrame:
    """Section 7.4 - short-leg P&L reliance on high-short-interest names."""
    oos = panel[panel["sample_split"].isin(s5.WINDOWS["oos_2019_2024"])].copy()
    rows = []
    for model in ("xgboost_only", "ridge_xgb_ensemble"):
        if model == "xgboost_only":
            scored, col = s5.add_xgb_score(oos), "score_xgb"
        else:
            scored, col = s5.add_ensemble_score(oos, cfg.w_ridge), "score_ensemble"
        rows.append({
            "model": model,
            "window": "oos_2019_2024",
            "si_threshold": si_threshold,
            **_borrow_honesty_one(scored, col, cfg, si_threshold),
        })
    return pd.DataFrame(rows)


def main() -> None:
    cfg = s5.Step5Config()
    print(f"Loading point-in-time panel (cutoff {cfg.cutoff})...")
    panel = s5.load_panel(cfg)
    print("  panel rows:", len(panel))

    # Q1 - validation selection for basket size / ensemble weight.
    w_best, q_best, grid = select_hyperparams(panel, cfg)
    grid.to_csv(OUT / "stage5_weight_quantile_selection.csv", index=False)
    cfg.w_ridge, cfg.quantile = w_best, q_best
    print(f"Selected on validation: w_ridge={w_best}, quantile={q_best}")

    basket_turnover_table(panel, cfg).to_csv(
        OUT / "stage5_q1_basket_turnover.csv", index=False
    )

    # Q2 - headline full-window XGBoost table + OOS ensemble robustness.
    headline, _ = headline_table(panel, cfg)
    headline.to_csv(OUT / "stage5_headline_performance.csv")
    ensemble_robustness(panel, cfg).to_csv(OUT / "stage5_ensemble_robustness.csv")
    print("\nHeadline net Sharpe (XGBoost-only) by window x AUM:")
    print(headline["net_sharpe"].unstack().round(2).to_string())

    # Common 250M frames for Q3/Q4/Q5.
    daily_250_headline = s5.run_window(
        panel, cfg, s5.WINDOWS["full_2010_2024"], 250_000_000, model="xgb"
    )
    daily_250_oos = s5.run_window(
        panel, cfg, s5.WINDOWS["oos_2019_2024"], 250_000_000, model="ensemble"
    )

    # Q3 - cost decomposition.
    s5.cost_decomposition(daily_250_headline).to_csv(
        OUT / "stage5_cost_decomposition_full_2010_2024_xgb_250M.csv"
    )
    s5.cost_decomposition(daily_250_oos).to_csv(
        OUT / "stage5_cost_decomposition_oos_2019_2024_ensemble_250M.csv"
    )

    # Q5 - stress windows.
    stress_headline = s5.stress_windows(daily_250_headline)
    stress_headline.insert(0, "model", "xgboost_only")
    stress_headline.insert(1, "sample", "full_2010_2024")
    stress_headline.to_csv(OUT / "stage5_stress_windows_full_2010_2024_xgb_250M.csv",
                           index=False)

    stress_oos = s5.stress_windows(daily_250_oos)
    stress_oos.insert(0, "model", "ridge_xgb_ensemble")
    stress_oos.insert(1, "sample", "oos_2019_2024")
    stress_oos.to_csv(OUT / "stage5_stress_windows_oos_2019_2024_ensemble_250M.csv",
                      index=False)

    # Section 7 diagnostics on both model variants over the OOS window.
    store_oos: DiagStore = {}
    for aum in cfg.aum_levels:
        store_oos[("oos_2019_2024", "xgboost_only", aum)] = s5.run_window(
            panel, cfg, s5.WINDOWS["oos_2019_2024"], aum, model="xgb"
        )
        store_oos[("oos_2019_2024", "ridge_xgb_ensemble", aum)] = s5.run_window(
            panel, cfg, s5.WINDOWS["oos_2019_2024"], aum, model="ensemble"
        )
    capacity_diagnostics(store_oos, cfg).to_csv(OUT / "stage5_capacity_diagnostics.csv",
                                                index=False)
    borrow_honesty(panel, cfg).to_csv(OUT / "stage5_borrow_honesty.csv", index=False)

    # Audit daily return series.
    daily_250_headline.to_csv(OUT / "stage5_daily_returns_full_2010_2024_xgb_250M.csv")
    daily_250_oos.to_csv(OUT / "stage5_daily_returns_oos_2019_2024_ensemble_250M.csv")

    # Q4 - QuantStats tear-sheets.
    bench = s5.load_benchmark(cfg)
    s5.make_tearsheet(
        daily_250_headline["ret_net"],
        bench,
        OUT / "stage5_tearsheet_250M_full_2010_2024_xgb.html",
        title="C2O Overnight L/S | XGBoost-only | 250M AUM | 2010-2024 | net of Section 6.3 costs",
    )
    s5.make_tearsheet(
        daily_250_oos["ret_net"],
        bench,
        OUT / "stage5_tearsheet_250M_oos_2019_2024_ensemble.html",
        title="C2O Overnight L/S | Ridge+XGB | 250M AUM | OOS 2019-2024 | net of Section 6.3 costs",
    )
    print("Done. Outputs in", OUT)


if __name__ == "__main__":
    main()
