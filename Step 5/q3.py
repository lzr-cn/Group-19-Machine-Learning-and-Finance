"""Section 6 - Q3: gross-to-net Sharpe degradation.



The brief-facing headline is the 250M XGBoost-only strategy over the full
2010-2024 development window. We also keep the 250M Ridge+XGBoost OOS ensemble
decomposition as a robustness diagnostic.
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
    decomp_headline = s5.cost_decomposition(daily_headline)
    decomp_headline.to_csv(OUT / "stage5_cost_decomposition_full_2010_2024_xgb_250M.csv")

    daily_oos = s5.run_window(
        panel, cfg, s5.WINDOWS["oos_2019_2024"], 250_000_000, model="ensemble"
    )
    decomp_oos = s5.cost_decomposition(daily_oos)
    decomp_oos.to_csv(OUT / "stage5_cost_decomposition_oos_2019_2024_ensemble_250M.csv")

    print("Headline gross -> net Sharpe degradation (250M, XGBoost-only, 2010-2024):")
    print(decomp_headline.round(3).to_string())
    print("\nRobustness gross -> net Sharpe degradation (250M, Ridge+XGB, OOS 2019-2024):")
    print(decomp_oos.round(3).to_string())


if __name__ == "__main__":
    main()
