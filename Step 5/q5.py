"""Section 6 - Q5: stress-window analysis.

Standalone: ``python q5.py``.

The headline stress table uses the 250M XGBoost-only strategy over 2010-2024.
The OOS Ridge+XGBoost ensemble stress table is retained as a robustness diagnostic.
"""
from __future__ import annotations

from pathlib import Path

import stage5_portfolio as s5

OUT = Path(__file__).resolve().parent / "Stage_5_portfolio_outputs"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    cfg = s5.Step5Config()
    panel = s5.load_panel(cfg)

    daily_headline = s5.run_window(
        panel, cfg, s5.WINDOWS["full_2010_2024"], 250_000_000, model="xgb"
    )
    stress_headline = s5.stress_windows(daily_headline)
    stress_headline.insert(0, "model", "xgboost_only")
    stress_headline.insert(1, "sample", "full_2010_2024")
    stress_headline.to_csv(OUT / "stage5_stress_windows_full_2010_2024_xgb_250M.csv", index=False)

    daily_oos = s5.run_window(
        panel, cfg, s5.WINDOWS["oos_2019_2024"], 250_000_000, model="ensemble"
    )
    stress_oos = s5.stress_windows(daily_oos)
    stress_oos.insert(0, "model", "ridge_xgb_ensemble")
    stress_oos.insert(1, "sample", "oos_2019_2024")
    stress_oos.to_csv(OUT / "stage5_stress_windows_oos_2019_2024_ensemble_250M.csv", index=False)

    print("Headline stress-window behaviour (250M, XGBoost-only, 2010-2024):")
    print(stress_headline.round(3).to_string(index=False))
    print("\nRobustness stress-window behaviour (250M, Ridge+XGB, OOS 2019-2024):")
    print(stress_oos.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
