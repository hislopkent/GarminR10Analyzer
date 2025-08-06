import pandas as pd
import pytest
from utils.data_utils import remove_outliers, derive_offline_distance, classify_shots

def test_remove_outliers_drops_extreme_values():
    df = pd.DataFrame({'Metric': [1, 2, 3, 100]})
    filtered = remove_outliers(df, ['Metric'])
    assert 100 not in filtered['Metric'].values


def test_remove_outliers_handles_missing_values():
    df = pd.DataFrame({'Metric': [1, 2, None, 3, 100]})
    filtered = remove_outliers(df, ['Metric'])
    assert 100 not in filtered['Metric'].values
    # Missing values should be retained
    assert filtered['Metric'].isna().sum() == 1


def test_remove_outliers_multiple_columns():
    df = pd.DataFrame({'A': [1, 1, 1, 1, 100], 'B': [1, 1, 1, 1, 1]})
    filtered = remove_outliers(df, ['A', 'B'])
    assert 100 not in filtered['A'].values
    assert len(filtered) == 4


def test_remove_outliers_groups_by_club():
    df = pd.DataFrame(
        {
            'club': ['Driver', 'Driver', 'Driver', 'Wedge', 'Wedge'],
            'carry': [200, 210, 50, 50, 52],
        }
    )
    filtered = remove_outliers(df, ['carry'])
    driver_carries = filtered[filtered['club'] == 'Driver']['carry']
    wedge_carries = filtered[filtered['club'] == 'Wedge']['carry']
    assert 50 not in driver_carries.values
    # Wedge distances should be preserved
    assert 50 in wedge_carries.values


def test_remove_outliers_custom_threshold():
    df = pd.DataFrame({'Metric': [1, 2, 3, 10]})
    tight = remove_outliers(df, ['Metric'], z_thresh=1.0)
    assert 10 not in tight['Metric'].values
    loose = remove_outliers(df, ['Metric'], z_thresh=10.0)
    assert 10 in loose['Metric'].values


def test_remove_outliers_isolation_forest():
    pytest.importorskip("sklearn")
    df = pd.DataFrame({'Metric': [10, 11, 9, 12, 10, 11, 9, 12, 10, 11, 10, 11, 9, 12, 10, 11, 9, 12, 10, 11, 50]})
    filtered = remove_outliers(df, ['Metric'], method='isolation', contamination=0.1)
    assert 50 not in filtered['Metric'].values


def test_remove_outliers_iqr_multiplier():
    df = pd.DataFrame({'Metric': [1, 1, 1, 2, 100]})
    tight = remove_outliers(df, ['Metric'], z_thresh=3.0, iqr_mult=1.0)
    assert 100 not in tight['Metric'].values
    loose = remove_outliers(df, ['Metric'], z_thresh=3.0, iqr_mult=200.0)
    assert 100 in loose['Metric'].values


def test_derive_offline_distance_from_side():
    df = pd.DataFrame({"Side Distance": [5, -3]})
    result = derive_offline_distance(df)
    assert "Offline" in result.columns
    assert result["Offline"].tolist() == [5, -3]


def test_derive_offline_distance_from_side_column():
    df = pd.DataFrame({"Side": [4, -2]})
    result = derive_offline_distance(df)
    assert "Offline" in result.columns
    assert result["Offline"].tolist() == [4, -2]


def test_classify_shots_labels_quality():
    df = pd.DataFrame({
        'Carry Distance': [200, 50, 205],
        'Offline': [0, 20, -2]
    })
    result = classify_shots(df)
    assert result['Quality'].tolist() == ['good', 'outlier', 'good']
