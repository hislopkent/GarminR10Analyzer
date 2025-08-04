import pandas as pd
from utils.practice_ai import analyze_club_stats, analyze_practice_session

def test_analyze_club_stats_ignores_outliers_and_reports_max():
    df = pd.DataFrame({
        "Club": ["7 Iron"] * 7,
        "Carry Distance": [150, 151, 152, 400, 149, 150, 151],
        "Smash Factor": [1.33, 1.34, 1.35, 1.20, 1.32, 1.33, 1.34],
    })
    result = analyze_club_stats(df, "7 Iron")
    assert result["max_good_carry"] == 152


def test_analyze_club_stats_can_disable_outlier_filter():
    df = pd.DataFrame({
        "Club": ["7 Iron"] * 6,
        "Carry Distance": [150, 151, 152, 400, 149, 150],
        "Smash Factor": [1.33, 1.34, 1.35, 1.20, 1.32, 1.33],
    })
    result = analyze_club_stats(df, "7 Iron", filter_outliers=False)
    assert result["max_good_carry"] == 400

def test_analyze_club_stats_detects_fat_trend():
    df = pd.DataFrame({
        "Club": ["Driver"] * 7,
        "Carry Distance": [230, 231, 229, 228, 232, 231, 229],
        "Smash Factor": [1.10, 1.12, 1.11, 1.13, 1.09, 1.10, 1.11],
    })
    result = analyze_club_stats(df, "Driver")
    assert any("fat or chunked" in issue for issue in result["issues"])


def test_analyze_practice_session_skips_clubs_with_few_shots():
    df = pd.DataFrame(
        {
            "Club": ["7 Iron"] * 7 + ["Driver"] * 5,
            "Carry Distance": [150, 151, 152, 153, 150, 151, 152, 230, 231, 229, 228, 232],
            "Smash Factor": [
                1.33,
                1.34,
                1.35,
                1.33,
                1.32,
                1.33,
                1.34,
                1.10,
                1.12,
                1.11,
                1.13,
                1.09,
            ],
        }
    )
    results = analyze_practice_session(df)
    clubs = [r["club"] for r in results]
    assert "7 Iron" in clubs and "Driver" not in clubs
