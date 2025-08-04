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
        # Use the full column for masking so index alignment is preserved
        series = coerce_numeric(filtered[col])
        valid = series.dropna()
        if valid.empty:
            continue
        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = series.between(lower, upper) | series.isna()
        filtered = filtered.loc[mask]
    return filtered


def derive_offline_distance(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` with an ``Offline`` column if possible.

    Garmin CSV exports are inconsistent in naming lateral dispersion metrics.
    Some provide ``Side`` or ``Side Distance`` instead of ``Offline``.  This
    helper inspects these alternate columns and, when found, copies the values
    into a new ``Offline`` column.  The input dataframe is not modified in
    place.
    """

    df = df.copy()
    offline_present = any(col in df.columns for col in ("Offline", "Offline Distance"))
    if offline_present:
        return df

    for col in ("Side Distance", "Side"):
        if col in df.columns:
            df["Offline"] = coerce_numeric(df[col])
            break

    return df
