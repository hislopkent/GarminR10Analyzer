import pandas as pd


def coerce_numeric(series, errors: str = "coerce"):
    """Return numeric values for ``series`` even if duplicates exist.

    When a :class:`pandas.DataFrame` contains duplicate column names, indexing a
    column (``df[col]``) returns another ``DataFrame`` rather than a
    ``Series``.  ``pd.to_numeric`` expects a one-dimensional input and will
    raise ``TypeError`` in this scenario.  This helper picks the first column if
    ``series`` is a ``DataFrame`` before coercing the values to numeric.
    """

    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return pd.to_numeric(series, errors=errors)


def remove_outliers(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Return ``df`` with outliers removed for the given ``cols``.

    Outliers are detected using the 1.5 * IQR rule for each column. Rows
    outside the acceptable range for any provided column are dropped. Columns
    that are not present in ``df`` are ignored. ``df`` is not modified in
    place.
    """

    filtered = df.copy()
    for col in cols:
        if col not in filtered.columns:
            continue
        series = coerce_numeric(filtered[col]).dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = series.between(lower, upper)
        filtered = filtered.loc[mask]
    return filtered
