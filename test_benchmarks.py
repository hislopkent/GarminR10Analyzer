# test_benchmarks.py

from utils.benchmarks import check_benchmark

def test_driver_benchmark_all_good():
    stats = {
        'Carry': 230,
        'Smash Factor': 1.46,
        'Launch Angle': 13,
        'Backspin': 2500
    }
    result = check_benchmark("Driver", stats)
    assert all("✅" in line for line in result)

def test_driver_benchmark_mixed():
    stats = {
        'Carry': 210,
        'Smash Factor': 1.42,
        'Launch Angle': 18,
        'Backspin': 1400
    }
    result = check_benchmark("Driver", stats)
    assert any("❌" in line for line in result)


def test_club_name_case_insensitive():
    """`check_benchmark` should match club names regardless of case."""
    stats = {
        'Carry': 230,
        'Smash Factor': 1.46,
        'Launch Angle': 13,
        'Backspin': 2500
    }
    result = check_benchmark("driver", stats)
    assert all("✅" in line for line in result)
