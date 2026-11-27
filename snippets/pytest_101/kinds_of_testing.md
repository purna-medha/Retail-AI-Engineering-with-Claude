# Kinds of Testing: Smoke, Unit, Mock, Integration, Regression

The [pytest quickstart](pytest_quickstart.md) taught how to write and run tests. This guide answers a different question: **which kind of test do I write, and when?** It uses the same tiny [`calculator.py`](calculator.py).

All examples are in [`test_kinds_of_testing.py`](test_kinds_of_testing.py). From the repository root:

```bash
uv run --with pytest pytest snippets/pytest_101/test_kinds_of_testing.py -v -rs
```

```text
test_smoke_calculator_works PASSED
test_unit_average PASSED
test_mock_convert_calls_rate_api_once PASSED
test_mock_simulates_api_failure PASSED
test_regression_divide_keeps_decimals PASSED
test_average_of_generator XFAIL
test_integration_claude_replies SKIPPED
SKIPPED [1] could not import 'anthropic': No module named 'anthropic'
=================== 5 passed, 1 skipped, 1 xfailed in 0.02s ====================
```

`-rs` prints the reason for each skipped test.

---

## The map

| Kind | Question it answers | Speed | Real services? |
| --- | --- | --- | --- |
| **Smoke** | Does it work at all? | Instant | Maybe |
| **Unit** | Is this one function correct? | Milliseconds | No |
| **Mock** | Does my code use its dependency correctly, and survive its failures? | Milliseconds | No (faked) |
| **Integration** | Do my code and the real service work together? | Seconds | Yes |
| **Regression** | Is a fixed bug still fixed? | Same as its kind | Depends |

Run the fast kinds on every change. Run the slow kinds before you share or deploy.

---

## 1 · Smoke test: does it work at all?

The name comes from hardware: switch the device on and check that no smoke comes out. A smoke test is shallow and fast. It doesn't prove the app is correct. It proves the app isn't broken so badly that other tests are pointless.

```python
@pytest.mark.smoke
def test_smoke_calculator_works():
    assert add(1, 1) == 2
    assert divide(4, 2) == 2
```

`@pytest.mark.smoke` is a **marker**: a label you can select by. Run only the smoke tests:

```bash
uv run --with pytest pytest snippets/pytest_101 -m smoke
```

```text
1 passed, 19 deselected in 0.01s
```

**In AI apps:** [`claude_101.py`](../claude_101.py) is a smoke test. It sends “Reply with only: API key works!” If that fails, nothing else that calls Claude will work, so check it first.

---

## 2 · Unit test: one function, on its own

```python
def test_unit_average():
    assert average([2, 4, 6]) == 4
```

A unit test calls one function with exact inputs and checks an exact output. No network, no files, no database. When it fails, you know which function to open. Most of your tests should be unit tests. The [quickstart](pytest_quickstart.md) covers them in depth: happy path, edge cases, error cases.

---

## 3 · Mock test: replace a dependency, then check how it was used

`convert_usd` calls `get_exchange_rate`, which stands in for an online API. A **mock** replaces that function for one test and records every call made to it.

### Check the call

```python
from unittest.mock import patch

def test_mock_convert_calls_rate_api_once():
    with patch("calculator.get_exchange_rate", return_value=83.5) as fake_rate:
        assert convert_usd(10, "INR") == 835.0
    fake_rate.assert_called_once_with("INR")
```

| Part | Meaning |
| --- | --- |
| `patch("calculator.get_exchange_rate", ...)` | Inside the `with` block, that function is replaced |
| `return_value=83.5` | The mock returns 83.5 whenever it's called |
| `assert_called_once_with("INR")` | Our code asked for INR, exactly once. Calling the paid API twice would be a bug |

### Simulate a failure

Real services time out, rate-limit and go down. You can't make a real API fail on demand, but a mock can:

```python
def test_mock_simulates_api_failure():
    with patch("calculator.get_exchange_rate", side_effect=TimeoutError("API timed out")):
        with pytest.raises(TimeoutError):
            convert_usd(10, "INR")
```

`side_effect` makes the mock raise an error instead of returning. The test checks what **our** code does when the service fails. Here the error passes straight through. If you later add retries or a friendly message, this is where you test them.

### Fake, stub or mock?

You'll hear all three words. The difference is small:

| Word | What it does | In this folder |
| --- | --- | --- |
| **Fake / stub** | Returns a fixed answer | `monkeypatch.setattr(..., lambda currency: 83.5)` in the quickstart |
| **Mock** | Returns a fixed answer **and** records the calls so you can check them | `patch(...)` with `assert_called_once_with` |

Use a fake when you only care about the result. Use a mock when *how* the dependency was called matters: which arguments, how many times.

**In AI apps:** mock the LLM call to test your prompt building, tool functions and response parsing for free. Check that the right prompt was sent, and that your code handles an empty reply or a rate-limit error.

---

## 4 · Integration test: use the real service

Mocks prove your code is right *if* the service behaves as you assumed. An integration test checks that assumption against the real thing.

```python
@pytest.mark.integration
def test_integration_claude_replies():
    anthropic = pytest.importorskip("anthropic")         # Skip if the library isn't installed.
    pytest.importorskip("dotenv").load_dotenv()          # Read CLAUDE_API_KEY from .env.
    if not os.getenv("CLAUDE_API_KEY"):
        pytest.skip("CLAUDE_API_KEY not set")
    ...
    assert "5" in text  # Check the fact, not the exact wording.
```

Integration tests are slow, need keys and a network, and can cost money. Three habits keep them under control:

| Habit | How |
| --- | --- |
| Label them | `@pytest.mark.integration` |
| Skip them cleanly when they can't run | `pytest.importorskip(...)`, `pytest.skip(...)` |
| Leave them out of the fast run | `pytest -m "not integration"` |

Run the real one, with the libraries and your key:

```bash
uv run --with pytest --with anthropic --with python-dotenv pytest snippets/pytest_101 -m integration -v
```

```text
test_kinds_of_testing.py::test_integration_claude_replies PASSED
======================= 1 passed, 19 deselected in 2.99s =======================
```

Three seconds for one test, against milliseconds for the others. That is why integration tests are kept few.

Notice the assertion: `"5" in text`, not `text == "5"`. Claude might reply “5” or “5.” An LLM test checks the fact, not the exact wording. When the fact is fuzzier than a number, that's what DeepEval evaluations are for.

---

## 5 · Regression test: a fixed bug stays fixed

In the quickstart, changing `/` to `//` in `divide` returned `0` for `1 / 4`. After fixing a bug like that, add a test that would have caught it:

```python
def test_regression_divide_keeps_decimals():
    # Bug found earlier: divide used // and returned 0 for 1 / 4.
    assert divide(1, 4) == 0.25
```

The comment records *why* the test exists, so nobody deletes it as redundant. Every bug you fix should leave a test behind. A suite of regression tests is how code gets safer over time.

**In AI apps:** the M10 goldens are regression tests for model behaviour. When the bot once called today's balance the “January closing balance”, that question became a golden, so the mistake can't quietly come back.

---

## 6 · Expected failure: a known bug, written down

```python
@pytest.mark.xfail(reason="average() does not accept a generator yet")
def test_average_of_generator():
    assert average(n for n in [2, 4]) == 3
```

`xfail` means “expected to fail”. The suite stays green, the bug stays visible in the report as `XFAIL`, and when someone fixes it, pytest reports `XPASS` so you know to remove the marker. Use it for known bugs, not to hide tests you don't want to fix.

---

## 7 · Coverage: which lines did no test run?

```bash
cd snippets/pytest_101
uv run --with pytest --with pytest-cov pytest --cov=calculator --cov-report=term-missing -m "not integration"
```

```text
Name            Stmts   Miss  Cover   Missing
calculator.py      21      1    95%   34
```

Line 34 is the body of `get_exchange_rate`: the real API call. Every unit and mock test replaced it, so it never ran. That is exactly right. Covering the real call is the integration test's job.

Coverage tells you what was **never run**, not what was **tested well**. A line can run in a test that checks nothing. Use the `Missing` column to find gaps; don't chase 100%.

---

## 8 · Flaky tests: same code, different results

A **flaky** test passes on one run and fails on the next with no code change. Common causes:

| Cause | Fix |
| --- | --- |
| Tests share state, so order matters | Fixtures that give each test a fresh object |
| Real network or service is slow or down | Mock it in unit tests; keep integration tests few and labelled |
| The output is random, like an LLM reply | Assert facts (`"5" in text`), not exact text; use evaluations for meaning |

A flaky test is worse than no test, because people learn to ignore red. If a test flips, find the cause. Don't just re-run until it's green.

---

## 9 · Choose the right test

| Situation | Write a… |
| --- | --- |
| You just set up a project or API key | Smoke test |
| You wrote a function with clear inputs and outputs | Unit test |
| Your code calls an API or LLM | Mock test for your logic, plus one integration test for the real call |
| You fixed a bug | Regression test that reproduces it |
| You found a bug you can't fix today | `xfail` test with a reason |
| You want to judge the *meaning* of an LLM answer | A DeepEval evaluation (M10) |

### Kinds of testing you can skip for now

These are real disciplines, but each needs systems or tools beyond a first AI application:

| Kind | What it checks |
| --- | --- |
| Load / performance | How the app behaves with many users or large inputs |
| Security / penetration | Whether attackers can break in or leak data |
| End-to-end UI | Clicking through the app in a real browser |
| Property-based | Hundreds of generated inputs (library: Hypothesis) |
| Mutation | Whether your tests catch deliberately injected bugs |
| Contract | Whether two services still agree on their API format |

You already did a small mutation test by hand: changing `/` to `//` and checking that a test caught it.
