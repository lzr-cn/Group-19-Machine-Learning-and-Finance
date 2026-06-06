from __future__ import annotations

from pathlib import Path
import pandas as pd

import stage5_portfolio as s5


OUT = Path(__file__).resolve().parent / "Stage_5_portfolio_outputs"
OUT.mkdir(parents=True, exist_ok=True)


def score_panel(panel: pd.DataFrame, cfg: s5.Step5Config, model: str) -> tuple[pd.DataFrame, str]:
    """
    Add the score used for ranking.

    model="xgb"      -> XGBoost-only score, available for full 2010--2024.
    model="ensemble" -> Ridge + XGBoost ensemble, valid mainly for 2019--2024.
    """
    if model == "xgb":
        scored = s5.add_xgb_score(panel)
        return scored, "score_xgb"

    if model == "ensemble":
        scored = s5.add_ensemble_score(panel, cfg.w_ridge)
        return scored, "score_ensemble"

    raise ValueError("model must be either 'xgb' or 'ensemble'")


def raw_short_borrow_affected(
    panel: pd.DataFrame,
    cfg: s5.Step5Config,
    window_name: str,
    splits: list[str],
    model: str = "xgb",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute the fraction of the raw short signal affected by borrow treatment.

    Raw short signal:
        bottom q names by score each day, before borrow fees and before cap sizing.

    Affected:
        borrow_tier is B or C.

    Tier C:
        borrow_tier is C.
    """
    sub = panel[panel["sample_split"].isin(splits)].copy()
    scored, score_col = score_panel(sub, cfg, model)

    daily_rows = []

    for date, day in scored.groupby("date", sort=True):
        day = day.dropna(subset=[score_col, "r_on_next", "borrow_tier"])
        if len(day) < 20:
            continue

        n_short = max(1, int(round(len(day) * cfg.quantile)))

        # Bottom q = raw short signal
        ordered = day.sort_values(score_col)
        shorts = ordered.iloc[:n_short].copy()

        is_affected = shorts["borrow_tier"].isin(["B", "C"])
        is_tier_c = shorts["borrow_tier"].eq("C")

        daily_rows.append({
            "date": date,
            "window": window_name,
            "model": model,
            "n_eligible": len(day),
            "n_raw_short": len(shorts),
            "affected_names": int(is_affected.sum()),
            "tier_c_names": int(is_tier_c.sum()),
            "affected_share": float(is_affected.mean()),
            "tier_c_share": float(is_tier_c.mean()),
        })

    daily = pd.DataFrame(daily_rows)

    total_short = daily["n_raw_short"].sum()
    total_affected = daily["affected_names"].sum()
    total_tier_c = daily["tier_c_names"].sum()

    summary = pd.DataFrame([{
        "window": window_name,
        "model": model,
        "quantile": cfg.quantile,
        "n_days": len(daily),
        "avg_raw_short_names_per_day": daily["n_raw_short"].mean(),
        "total_raw_short_stockdays": total_short,
        "tier_b_or_c_stockdays": total_affected,
        "tier_c_stockdays": total_tier_c,

        # This is the main number for Step 3 Q3
        "raw_short_signal_affected_pct": 100 * total_affected / total_short,
        "raw_short_signal_tier_c_pct": 100 * total_tier_c / total_short,

        # Daily-average version, useful as a robustness check
        "avg_daily_affected_pct": 100 * daily["affected_share"].mean(),
        "avg_daily_tier_c_pct": 100 * daily["tier_c_share"].mean(),
    }])

    return summary, daily


def main() -> None:
    cfg = s5.Step5Config()
    panel = s5.load_panel(cfg)

    jobs = [
        # Headline model: XGBoost-only
        ("full_2010_2024", s5.WINDOWS["full_2010_2024"], "xgb"),
        ("oos_2019_2024", s5.WINDOWS["oos_2019_2024"], "xgb"),
        ("test_2022_2024", s5.WINDOWS["test_2022_2024"], "xgb"),

        # Robustness model: ensemble, only meaningful where Ridge exists
        ("oos_2019_2024", s5.WINDOWS["oos_2019_2024"], "ensemble"),
        ("test_2022_2024", s5.WINDOWS["test_2022_2024"], "ensemble"),
    ]

    summaries = []
    dailies = []

    for window_name, splits, model in jobs:
        summary, daily = raw_short_borrow_affected(
            panel=panel,
            cfg=cfg,
            window_name=window_name,
            splits=splits,
            model=model,
        )
        summaries.append(summary)
        dailies.append(daily)

    summary_all = pd.concat(summaries, ignore_index=True)
    daily_all = pd.concat(dailies, ignore_index=True)

    summary_path = OUT / "stage5_raw_short_borrow_affected_summary.csv"
    daily_path = OUT / "stage5_raw_short_borrow_affected_daily.csv"

    summary_all.to_csv(summary_path, index=False)
    daily_all.to_csv(daily_path, index=False)

    print("\nRaw short signal affected by borrow treatment")
    print(summary_all.round(3).to_string(index=False))
    print(f"\nSaved summary to: {summary_path}")
    print(f"Saved daily data to: {daily_path}")


if __name__ == "__main__":
    main()