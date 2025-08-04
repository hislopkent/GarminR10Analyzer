import pandas as pd
from utils.data_utils import remove_outliers

def test_remove_outliers_drops_extreme_values():
    df = pd.DataFrame({'Metric': [1, 2, 3, 100]})
    filtered = remove_outliers(df, ['Metric'])
    assert 100 not in filtered['Metric'].values
