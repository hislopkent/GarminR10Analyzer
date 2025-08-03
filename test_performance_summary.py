import pandas as pd

from utils.performance_summary import summarize_performance


def _sample_df():
    return pd.DataFrame(
        {
            "Club Type": ["7 Iron", "7 Iron", "Driver", "Driver", "7 Iron"],
            "Carry Distance": [140, 142, 230, 235, 138],
            "Smash Factor": [1.20, 1.25, 1.45, 1.48, 1.18],
            "Launch Angle": [14, 15, 13, 12, 16],
            "Backspin": [6000, 6200, 2500, 2600, 5800],
            "Offline": [10, -8, 30, -20, 12],
        }
    )


def test_summary_contains_miss_and_drill():
    df = _sample_df()
    summary = summarize_performance(df)
    assert "Most common miss" in summary
    assert "needs attention" in summary
    assert "Practice tip" in summary

