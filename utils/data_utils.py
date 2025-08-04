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

    The 1.5 * IQR rule is applied per column. When a club column (``club`` or
    ``Club``) is present, the rule is evaluated within each club so that
    legitimate shots for one club are not discarded because of another club's
    distances. Rows falling outside the acceptable range for **any** provided
    column are dropped. Columns not present in ``df`` are ignored. ``df`` is
    not modified in place.
    """

    filtered = df.copy()
    group_col = next((c for c in ("club", "Club") if c in filtered.columns), None)

    def _mask(series: pd.Series) -> pd.Series:
        valid = series.dropna()
        if len(valid) < 3:
            return pd.Series(True, index=series.index)
        median = valid.median()
        mad = (valid - median).abs().median()
        if mad > 0:
            z = 0.6745 * (series - median) / mad
            return (z.abs() <= 3) | series.isna()
        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return series.between(lower, upper) | series.isna()

    masks = []
    for col in cols:
        if col not in filtered.columns:
            continue
        series = coerce_numeric(filtered[col])
        if group_col:
            mask = filtered.groupby(group_col)[col].transform(lambda s: _mask(s))
        else:
            mask = _mask(series)
        masks.append(mask)

    if masks:
        combined = pd.concat(masks, axis=1).all(axis=1)
        filtered = filtered.loc[combined]

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
