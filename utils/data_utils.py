"""Utility helpers for working with Garmin shot data."""

import pandas as pd

try:  # scikit-learn is optional
    from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover - handled at runtime
    IsolationForest = None


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
    method: str = "mad",
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
    method:
        Outlier detection approach. ``"mad"`` applies a robust z-score rule
        with an IQR fallback. ``"isolation"`` uses an Isolation Forest for
        adaptive, multivariate detection.

    When a club column (``club`` or ``Club``) is present the outlier rule is
    evaluated within each club.  Rows falling outside the acceptable range for
    **any** provided column are dropped. Columns not present in ``df`` are
    ignored. ``df`` is not modified in place.
    """

    filtered = df.copy()
    cols = [c for c in cols if c in filtered.columns]
    if not cols:
        return filtered

    numeric = filtered[cols].apply(coerce_numeric)
    group_col = next((c for c in ("club", "Club") if c in filtered.columns), None)

    if method == "isolation":
        if IsolationForest is None:
            raise ImportError("scikit-learn is required for adaptive outlier detection")
        mask = pd.Series(True, index=filtered.index)
        if group_col:
            for _, idx in numeric.groupby(filtered[group_col]).groups.items():
                subset = numeric.loc[idx]
                if len(subset) < 2:
                    continue
                model = IsolationForest(contamination="auto", random_state=0)
                preds = model.fit_predict(subset)
                mask.loc[idx] = preds == 1
        else:
            if len(numeric) >= 2:
                model = IsolationForest(contamination="auto", random_state=0)
                preds = model.fit_predict(numeric)
                mask = preds == 1
        return filtered[mask]

    # default: robust z-score with IQR fallback
    if group_col:
        groups = filtered[group_col]

        def _mad(x: pd.Series) -> float:
            return (x - x.median()).abs().median()

        _mad.__name__ = "mad"  # naming for groupby.agg

        def _q1(x: pd.Series) -> float:
            return x.quantile(0.25)

        _q1.__name__ = "q1"

        def _q3(x: pd.Series) -> float:
            return x.quantile(0.75)

        _q3.__name__ = "q3"

        stats = numeric.groupby(groups).agg(["median", _mad, _q1, _q3])
        stats.columns = [f"{col}_{stat}" for col, stat in stats.columns]
        stats = stats.reindex(groups).set_index(filtered.index)
        median = stats[[f"{c}_median" for c in cols]]
        median.columns = cols
        mad = stats[[f"{c}_mad" for c in cols]]
        mad.columns = cols
        q1 = stats[[f"{c}_q1" for c in cols]]
        q1.columns = cols
        q3 = stats[[f"{c}_q3" for c in cols]]
        q3.columns = cols
    else:
        median = numeric.median()
        mad = (numeric - median).abs().median()
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)

    z = 0.6745 * (numeric - median) / mad.replace(0, pd.NA)
    z_mask = z.abs().le(z_thresh)

    iqr = q3 - q1
    lower = q1 - iqr_mult * iqr
    upper = q3 + iqr_mult * iqr
    iqr_mask = (numeric >= lower) & (numeric <= upper)

    mask = z_mask | (mad.eq(0) & iqr_mask) | numeric.isna()
    return filtered[mask.all(axis=1)]


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
    df["Quality"] = "good"

    median = mad = None
    if carry_col in df.columns:
        df[carry_col] = coerce_numeric(df[carry_col])
        median = df[carry_col].median()
        mad = (df[carry_col] - median).abs().median()

    offline_abs = None
    if offline_col in df.columns:
        df[offline_col] = coerce_numeric(df[offline_col])
        offline_abs = df[offline_col].abs()
        df.loc[offline_abs > 15, "Quality"] = "outlier"

    if carry_col in df.columns and mad is not None and mad > 0:
        z = 0.6745 * (df[carry_col] - median) / mad
        df.loc[z.abs() > 3, "Quality"] = "outlier"

    miss_mask = pd.Series(False, index=df.index)
    if carry_col in df.columns:
        miss_mask |= (df[carry_col] - median).abs() > 10
    if offline_abs is not None:
        miss_mask |= offline_abs > 7

    df.loc[miss_mask & df["Quality"].eq("good"), "Quality"] = "miss"
    return df
