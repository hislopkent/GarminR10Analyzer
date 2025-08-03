import pandas as pd

from utils.drill_recommendations import recommend_drills


def test_recommends_low_smash():
    df = pd.DataFrame({
        'Club Type': ['Driver', 'Driver'],
        'Carry Distance': [230, 232],
        'Smash Factor': [1.40, 1.46],
        'Launch Angle': [12, 13],
    })
    recs = recommend_drills(df)
    issues = [r.issue for r in recs['Driver']]
    assert "Low smash factor" in issues


def test_no_issues_for_good_pw():
    df = pd.DataFrame({
        'Club Type': ['PW', 'PW'],
        'Carry Distance': [120, 121],
        'Smash Factor': [1.26, 1.27],
        'Launch Angle': [26, 27],
    })
    recs = recommend_drills(df)
    assert recs['PW'] == []


def test_inconsistent_carry():
    df = pd.DataFrame({
        'Club Type': ['7 Iron'] * 3,
        'Carry Distance': [130, 150, 170],
        'Smash Factor': [1.33, 1.34, 1.32],
        'Launch Angle': [16, 17, 18],
    })
    recs = recommend_drills(df)
    issues = [r.issue for r in recs['7 Iron']]
    assert "Inconsistent carry distance" in issues


def test_poor_launch_angle():
    df = pd.DataFrame({
        'Club Type': ['7 Iron'] * 2,
        'Carry Distance': [150, 152],
        'Smash Factor': [1.33, 1.34],
        'Launch Angle': [25, 26],
    })
    recs = recommend_drills(df)
    issues = [r.issue for r in recs['7 Iron']]
    assert "Poor launch angle" in issues


def test_high_launch_wedge():
    df = pd.DataFrame({
        'Club Type': ['PW', 'PW'],
        'Carry Distance': [100, 101],
        'Smash Factor': [1.26, 1.27],
        'Launch Angle': [45, 46],
    })
    recs = recommend_drills(df)
    issues = [r.issue for r in recs['PW']]
    assert "Launch angle too high with wedge" in issues


def test_excessive_wedge_backspin():
    df = pd.DataFrame({
        'Club Type': ['PW', 'PW'],
        'Carry Distance': [100, 102],
        'Smash Factor': [1.26, 1.27],
        'Launch Angle': [30, 31],
        'Backspin': [12000, 12500],
    })
    recs = recommend_drills(df)
    issues = [r.issue for r in recs['PW']]
    assert "Excessive wedge backspin" in issues
