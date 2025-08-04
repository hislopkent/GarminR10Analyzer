import pandas as pd
from utils.data_utils import remove_outliers, derive_offline_distance

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
