"""Section 6 - Q4: QuantStats tear-sheets versus SP500_TR.

The required deliverable is the 250M XGBoost-only strategy over 2010-2024.
An OOS Ridge+XGBoost ensemble tear-sheet is also rendered as a robustness diagnostic.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless, deterministic rendering

from pathlib import Path

import stage5_portfolio as s5

OUT = Path(__file__).resolve().parent / "Stage_5_portfolio_outputs"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    cfg = s5.Step5Config()
    panel = s5.load_panel(cfg)
    bench = s5.load_benchmark(cfg)

    daily_headline = s5.run_window(
        panel, cfg, s5.WINDOWS["full_2010_2024"], 250_000_000, model="xgb"
    )
    headline_html = OUT / "stage5_tearsheet_250M_full_2010_2024_xgb.html"
    s5.make_tearsheet(
        daily_headline["ret_net"],
        bench,
        headline_html,
        title="C2O Overnight L/S | XGBoost-only | 250M AUM | 2010-2024 | net of Section 6.3 costs",
    )

    daily_oos = s5.run_window(
        panel, cfg, s5.WINDOWS["oos_2019_2024"], 250_000_000, model="ensemble"
    )
    oos_html = OUT / "stage5_tearsheet_250M_oos_2019_2024_ensemble.html"
    s5.make_tearsheet(
        daily_oos["ret_net"],
        bench,
        oos_html,
        title="C2O Overnight L/S | Ridge+XGB | 250M AUM | OOS 2019-2024 | net of Section 6.3 costs",
    )

    print("Headline tear-sheet written:", headline_html)
    print("Robustness tear-sheet written:", oos_html)


if __name__ == "__main__":
    main()
