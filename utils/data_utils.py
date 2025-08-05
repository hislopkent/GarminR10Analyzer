"""Utility helpers for working with Garmin shot data."""

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


def remove_outliers(
    df: pd.DataFrame,
    cols: list[str],
    *,
    z_thresh: float = 3.0,
    iqr_mult: float = 1.5,
) -> pd.DataFrame:
    """Return ``df`` with outliers removed for the given ``cols``.

    Parameters
    ----------
    df:
        Input dataframe.
    cols:
        Columns to evaluate for outliers.
    z_thresh:
        Z-score threshold based on the median absolute deviation.  The default
        is ``3`` which is roughly equivalent to Tukey's 1.5 * IQR rule.
    iqr_mult:
        Multiplier for the IQR fallback when MAD is zero.  A value of ``1.5``
        matches the conventional IQR rule.

    When a club column (``club`` or ``Club``) is present the outlier rule is
    evaluated within each club.  Rows falling outside the acceptable range for
    **any** provided column are dropped. Columns not present in ``df`` are
    ignored. ``df`` is not modified in place.
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
            return (z.abs() <= z_thresh) | series.isna()
        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_mult * iqr
        upper = q3 + iqr_mult * iqr
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


def classify_shots(
    df: pd.DataFrame,
    carry_col: str = "Carry Distance",
    offline_col: str = "Offline",
) -> pd.DataFrame:
    """Return ``df`` with a ``Quality`` column describing shot quality.

    Shots are labelled ``good``, ``miss`` or ``outlier`` based on simple
    heuristics of carry distance consistency and lateral dispersion. Existing
    ``Quality`` values are overwritten. The input dataframe is not modified in
    place.
    """

    df = df.copy()
    if carry_col in df.columns:
        df[carry_col] = coerce_numeric(df[carry_col])
        median = df[carry_col].median()
        mad = (df[carry_col] - median).abs().median()
    else:
        median = mad = None
    if offline_col in df.columns:
        df[offline_col] = coerce_numeric(df[offline_col])

    def _label(row: pd.Series) -> str:
        carry = row.get(carry_col)
        offline = row.get(offline_col)
        if pd.notna(offline) and abs(offline) > 15:
            return "outlier"
        if median is not None and pd.notna(carry):
            if mad and mad > 0:
                z = 0.6745 * (carry - median) / mad
                if abs(z) > 3:
                    return "outlier"
            if abs(carry - median) > 10 or (
                pd.notna(offline) and abs(offline) > 7
            ):
                return "miss"
        return "good"

    df["Quality"] = df.apply(_label, axis=1)
    return df
