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


def test_derive_offline_distance_from_side():
    df = pd.DataFrame({"Side Distance": [5, -3]})
    result = derive_offline_distance(df)
    assert "Offline" in result.columns
    assert result["Offline"].tolist() == [5, -3]
