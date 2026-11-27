# Tests for calculator.py. Run: uv run --with pytest pytest snippets/pytest_101 -v
import pytest

import calculator
from calculator import Calculator, add, average, convert_usd, divide

# 1 · A test is a function named test_... that asserts what should be true.
def test_add_two_numbers():
    result = add(2, 3)      # Act: call the code.
    assert result == 5      # Assert: check the result.

# 2 · Edge cases: zero, negatives, and other inputs at the edges.
def test_add_negative_numbers():
    assert add(-2, -3) == -5

def test_average_of_one_number():
    assert average([7]) == 7

# 3 · Error cases: the code should refuse bad input with a clear error.
def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="divide by zero"):
        divide(10, 0)

def test_average_of_empty_list_raises():
    with pytest.raises(ValueError):
        average([])

# 4 · Floats are approximate: 0.1 + 0.2 is 0.30000000000000004.
def test_add_floats():
    assert add(0.1, 0.2) == pytest.approx(0.3)

# 5 · Parametrize: one test, many input/expected pairs.
@pytest.mark.parametrize("a, b, expected", [
    (10, 2, 5),
    (9, 3, 3),
    (-8, 2, -4),
    (1, 4, 0.25),
])
def test_divide(a, b, expected):
    assert divide(a, b) == expected

# 6 · Fixtures: shared setup. Each test gets its own fresh Calculator.
@pytest.fixture
def calc():
    return Calculator()  # Arrange: build the starting state.

def test_history_records_result(calc):
    calc.add(2, 3)
    assert calc.history == [5]

def test_history_starts_empty(calc):
    assert calc.history == []  # Passes because the fixture gives a new Calculator.

# 7 · Fakes: replace a slow or paid call (an API, an LLM) with a fixed answer.
def test_convert_usd_with_fake_rate(monkeypatch):
    monkeypatch.setattr(calculator, "get_exchange_rate", lambda currency: 83.5)
    assert convert_usd(10, "INR") == 835.0
