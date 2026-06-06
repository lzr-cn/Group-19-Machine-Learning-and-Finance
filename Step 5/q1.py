"""Section 6 · Q1 - basket sizes, in-basket weighting scheme, average daily turnover.

Owns the validation hyper-parameter search (which justifies the basket size) and the
turnover report. Depends on the shared engine (stage5_portfolio.py).
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path

import pandas as pd

import stage5_portfolio as s5

OUT = Path(__file__).resolve().parent / "Stage_5_portfolio_outputs"
OUT.mkdir(parents=True, exist_ok=True)

# Hyper-parameter search grids (searched on the VALIDATION split only) - a Q1 choice.
W_GRID: tuple[float, ...] = (0.0, 0.3, 0.5, 0.7, 1.0)
Q_GRID: tuple[float, ...] = (0.02, 0.03, 0.05, 0.10)


def select_hyperparams(panel: pd.DataFrame, cfg: s5.Step5Config,
                       aum: int = 250_000_000) -> tuple[float, float, pd.DataFrame]:
    """Joint (w_ridge, quantile) search by net Sharpe on the validation split (Q1)."""
    valid = panel[panel["sample_split"] == "valid"].copy()
    rows = []
    for w in W_GRID:
        scored = s5.add_ensemble_score(valid, w)
        for q in Q_GRID:
            trial_cfg = replace(cfg, quantile=q)
            daily = s5.backtest(scored, aum, trial_cfg)
            rows.append({"w_ridge": w, "quantile": q,
                         "valid_net_sharpe": s5._ann_sharpe(daily["ret_net"]),
                         "valid_gross_sharpe": s5._ann_sharpe(daily["ret_gross"])})
    grid = pd.DataFrame(rows)
    best = grid.sort_values(["valid_net_sharpe", "valid_gross_sharpe"],
                            ascending=False).iloc[0]
    return float(best["w_ridge"]), float(best["quantile"]), grid


def assert_config_in_sync(w_best: float, q_best: float) -> None:
    """Fail loudly if the validation-selected hyper-params drift from Step5Config defaults.

    q2.py / q3.py / q4.py / q5.py run on the Step5Config DEFAULTS - they do not re-run the
    selection - so those defaults must equal what validation actually selects. This guard
    turns any drift into a hard error instead of a silent inconsistency the marker would hit.
    """
    d = s5.Step5Config()
    assert abs(q_best - d.quantile) < 1e-12, (
        f"quantile drift: validation selected {q_best} but Step5Config.quantile default is "
        f"{d.quantile}. Update the default so q2-q5 (which use it) stay consistent.")
    assert abs(w_best - d.w_ridge) < 1e-12, (
        f"w_ridge drift: validation selected {w_best} but Step5Config.w_ridge default is "
        f"{d.w_ridge}. Update the default so the ensemble robustness stays consistent.")


def basket_turnover_table(panel: pd.DataFrame, cfg: s5.Step5Config) -> pd.DataFrame:
    """Actual basket sizes and daily turnover for the headline XGBoost OOS strategy."""
    rows = []
    for aum in cfg.aum_levels:
        daily = s5.run_window(panel, cfg, s5.WINDOWS["oos_2019_2024"], aum, model="xgb")
        rows.append({
            "aum": aum,
            "model": "xgboost_only",
            "window": "oos_2019_2024",
            "quantile": cfg.quantile,
            "median_names_per_side": int(daily["n_long"].median()),
            "min_names_per_side": int(daily["n_long"].min()),
            "max_names_per_side": int(daily["n_long"].max()),
            "weighting": "equal weight + participation-cap redistribution",
            "avg_daily_turnover": float(daily["turnover"].mean()),
            "avg_gross_exposure": float(daily["gross_exposure"].mean()),
        })
    return pd.DataFrame(rows)


def main() -> None:
    cfg = s5.Step5Config()
    panel = s5.load_panel(cfg)

    # Basket size + ensemble weight are chosen on VALIDATION only (net Sharpe).
    w_best, q_best, grid = select_hyperparams(panel, cfg)
    grid.to_csv(OUT / "stage5_weight_quantile_selection.csv", index=False)
    # Guard: q2-q5 use the Step5Config defaults, so they must equal the selected values.
    assert_config_in_sync(w_best, q_best)
    cfg.w_ridge, cfg.quantile = w_best, q_best

    # Average daily turnover (one-way notional / AUM) at each AUM level, full OOS.
    summary = basket_turnover_table(panel, cfg)
    summary.to_csv(OUT / "stage5_q1_basket_turnover.csv", index=False)

    print(f"Selected on validation: w_ridge={w_best}, quantile={q_best}")
    print(f"Basket: top/bottom {q_best:.0%} of the eligible cross-section, "
          "equal-weighted with participation-cap redistribution.")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
