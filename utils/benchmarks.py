"""Benchmark targets for typical golfer performance metrics."""


def get_benchmarks():
    """Return a dictionary of per-club benchmark targets."""
    return {
        "Driver": {
            "Carry": 220,
            "Smash Factor": 1.45,
            "Launch Angle": (10, 16),
            "Backspin": (1500, 3500)
        },
        "3 Hybrid": {
            "Carry": 200,
            "Smash Factor": 1.40,
            "Launch Angle": (11, 18),
            "Backspin": (3000, 5000)
        },
        "7 Iron": {
            "Carry": 150,
            "Smash Factor": 1.33,
            "Launch Angle": (15, 20),
            "Backspin": (5000, 7000)
        },
        "PW": {
            "Smash Factor": 1.25,
            "Backspin": (8000, 11000)
        },
        "SW": {
            "Backspin": (9000, 12000)
        }
    }

def check_benchmark(club_name, stats):
    """Compare ``stats`` for ``club_name`` against benchmark ranges."""

    benchmarks = get_benchmarks()
    result_lines = []

    target_type = None
    # Perform a case-insensitive lookup for the club name.  Garmin data
    # sometimes provides club names in lowercase (e.g. "driver") or with
    # different capitalisation.  Additionally, some names such as
    # "Pitching Wedge" are written out in full rather than using the
    # abbreviations stored in ``benchmarks``.  Normalising both strings and
    # handling a few common aliases avoids the function thinking a club has
    # no benchmark available.
    club_name_lower = club_name.lower()
    aliases = {"pitching wedge": "pw", "sand wedge": "sw"}
    for alias, repl in aliases.items():
        if alias in club_name_lower:
            club_name_lower = club_name_lower.replace(alias, repl)
            break

    for key in benchmarks:
        if key.lower() in club_name_lower:
            target_type = key
            break

    if not target_type:
        return ["No benchmark available for this club."]

    for metric, threshold in benchmarks[target_type].items():
        user_val = stats.get(metric)
        # ``stats`` may contain strings or other non-numeric values. Attempt to
        # coerce to ``float`` and skip the metric entirely if that fails so we
        # don't raise ``TypeError`` when formatting or comparing.
        try:
            user_val = float(user_val)
        except (TypeError, ValueError):
            continue

        if isinstance(threshold, tuple):
            low, high = threshold
            symbol = "✅" if low <= user_val <= high else "❌"
            result_lines.append(
                f"{metric}: {symbol} (You: {user_val:.1f}, Target: {low}–{high})"
            )
        else:
            symbol = "✅" if user_val >= threshold else "❌"
            result_lines.append(
                f"{metric}: {symbol} (You: {user_val:.1f}, Target: ≥{threshold})"
            )
    return result_lines
