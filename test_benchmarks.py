# test_benchmarks.py

import pytest

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


def test_driver_case_insensitive():
    """Benchmark lookup should be case-insensitive."""
    stats = {
        'Carry': 230,
        'Smash Factor': 1.46,
        'Launch Angle': 13,
        'Backspin': 2500,
    }
    result = check_benchmark("driver", stats)
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


def test_no_benchmark_available():
    """Return message for clubs without benchmarks."""
    stats = {'Carry': 100}
    result = check_benchmark("Putter", stats)
    assert result == ["No benchmark available for this club."]


@pytest.mark.parametrize(
    "stats, all_pass",
    [
        (
            {
                'Carry': 150,
                'Smash Factor': 1.33,
                'Launch Angle': 17,
                'Backspin': 6000,
            },
            True,
        ),
        (
            {
                'Carry': 140,
                'Smash Factor': 1.30,
                'Launch Angle': 22,
                'Backspin': 4000,
            },
            False,
        ),
    ],
)
def test_7_iron_benchmarks(stats, all_pass):
    """Check benchmarks for 7 Iron with passing and failing metrics."""
    result = check_benchmark("7 Iron", stats)
    if all_pass:
        assert all("✅" in line for line in result)
    else:
        assert any("❌" in line for line in result)
