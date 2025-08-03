# benchmarks.py

def get_benchmarks():
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
    benchmarks = get_benchmarks()
    result_lines = []

    # Normalize club name for case-insensitive matching. The original
    # implementation performed a direct substring check which failed for
    # club names using different capitalization (e.g. "driver" vs
    # "Driver").
    target_type = None
    club_name_lower = club_name.lower()
    for key in benchmarks:
        if key.lower() in club_name_lower:
            target_type = key
            break

    if not target_type:
        return ["No benchmark available for this club."]

    for metric, threshold in benchmarks[target_type].items():
        user_val = stats.get(metric)
        if user_val is None:
            continue
        if isinstance(threshold, tuple):
            low, high = threshold
            symbol = "✅" if low <= user_val <= high else "❌"
            result_lines.append(f"{metric}: {symbol} (You: {user_val:.1f}, Target: {low}–{high})")
        else:
            symbol = "✅" if user_val >= threshold else "❌"
            result_lines.append(f"{metric}: {symbol} (You: {user_val:.1f}, Target: ≥{threshold})")
    return result_lines
