# Kinds of testing, on the same tiny calculator.
# Run: uv run --with pytest pytest snippets/pytest_101/test_kinds_of_testing.py -v
import os
from unittest.mock import patch

import pytest

from calculator import add, average, convert_usd, divide


# 1 · Smoke test: the fastest check that the basics work at all. Run it first: pytest -m smoke
@pytest.mark.smoke
def test_smoke_calculator_works():
    assert add(1, 1) == 2
    assert divide(4, 2) == 2


# 2 · Unit test: one function, on its own, with exact inputs and outputs.
def test_unit_average():
    assert average([2, 4, 6]) == 4


# 3 · Mock test: replace the API call, then check HOW the code used it.
def test_mock_convert_calls_rate_api_once():
    with patch("calculator.get_exchange_rate", return_value=83.5) as fake_rate:
        assert convert_usd(10, "INR") == 835.0
    fake_rate.assert_called_once_with("INR")  # Asked for the right currency, exactly once.


def test_mock_simulates_api_failure():
    with patch("calculator.get_exchange_rate", side_effect=TimeoutError("API timed out")):
        with pytest.raises(TimeoutError):
            convert_usd(10, "INR")  # What does OUR code do when the service fails?


# 4 · Regression test: a bug that was fixed once must stay fixed.
def test_regression_divide_keeps_decimals():
    # Bug found earlier: divide used // and returned 0 for 1 / 4.
    assert divide(1, 4) == 0.25


# 5 · Expected failure: a known bug, written down but not fixed yet.
@pytest.mark.xfail(reason="average() does not accept a generator yet")
def test_average_of_generator():
    assert average(n for n in [2, 4]) == 3


# 6 · Integration test: talk to the real service. Slow and costs money, so it is marked and skippable.
@pytest.mark.integration
def test_integration_claude_replies():
    anthropic = pytest.importorskip("anthropic")         # Skip if the library isn't installed.
    pytest.importorskip("dotenv").load_dotenv()          # Read CLAUDE_API_KEY from .env.
    if not os.getenv("CLAUDE_API_KEY"):
        pytest.skip("CLAUDE_API_KEY not set")
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    reply = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": "What is 2 + 3? Reply with the number only."}],
    )
    text = "".join(block.text for block in reply.content if block.type == "text")
    assert "5" in text  # Check the fact, not the exact wording.
