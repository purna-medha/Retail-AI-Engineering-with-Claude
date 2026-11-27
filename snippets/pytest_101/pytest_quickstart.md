# pytest Quickstart: Testing a Tiny Calculator

A test is code that checks your code. You write down what *should* happen, run it, and the computer tells you if it still does — today, tomorrow, and after every change.

This guide uses a deliberately tiny calculator so all your attention goes to **testing**, not to the code being tested.

| File | What it is |
| --- | --- |
| [`calculator.py`](calculator.py) | The code under test: `add`, `divide`, `average`, a `Calculator` with history, and a currency converter |
| [`test_calculator.py`](test_calculator.py) | 13 tests that cover every idea in this guide |

---

## 1 · Run the tests

From the repository root:

```bash
uv run --with pytest pytest snippets/pytest_101 -v
```

```text
test_calculator.py::test_add_two_numbers PASSED
test_calculator.py::test_add_negative_numbers PASSED
...
test_calculator.py::test_convert_usd_with_fake_rate PASSED
============================== 13 passed in 0.02s ==============================
```

`-v` (verbose) prints one line per test. Without it you get one dot per passing test.

---

## 2 · A test is a function with an `assert`

```python
from calculator import add

def test_add_two_numbers():
    result = add(2, 3)   # Act: call the code
    assert result == 5   # Assert: check the result
```

`assert` says "this must be true". If it is, the test passes. If not, the test fails and pytest shows you why.

Most tests follow three steps, called **Arrange, Act, Assert**:

| Step | Meaning | Example |
| --- | --- | --- |
| Arrange | Set up what the test needs | `calc = Calculator()` |
| Act | Call the code you're testing | `calc.add(2, 3)` |
| Assert | Check the result | `assert calc.history == [5]` |

---

## 3 · How pytest finds tests

pytest only runs what matches its naming rules:

| Rule | Example |
| --- | --- |
| File name starts with `test_` (or ends with `_test.py`) | `test_calculator.py` |
| Function name starts with `test_` | `def test_add_two_numbers():` |

A function named `check_add()` is **ignored**, even if the file is run directly:

```text
collected 0 items
============================ no tests ran in 0.00s =============================
```

If you see "no tests ran" (or DeepEval's "No test cases found"), check the names first.

---

## 4 · Read a failure

Change the expected value to something wrong and run again:

```python
def test_add_two_numbers():
    assert add(2, 3) == 6
```

```text
    def test_add_two_numbers():
>       assert add(2, 3) == 6
E       assert 5 == 6
E        +  where 5 = add(2, 3)

test_fail.py:4: AssertionError
```

Read it from the bottom up:

- **`test_fail.py:4`** — the file and line that failed.
- **`assert 5 == 6`** — what the code returned (5) versus what you expected (6).
- **`where 5 = add(2, 3)`** — which call produced the value.

Now decide: is the **code** wrong, or is the **test** wrong? Here the test is wrong; 2 + 3 is 5.

---

## 5 · What to test: happy path, edge cases, errors

One test for the normal case is not enough. Bugs live at the edges.

| Kind of case | Question | Example in `test_calculator.py` |
| --- | --- | --- |
| **Happy path** | Does the normal case work? | `add(2, 3) == 5` |
| **Edge case** | What about zero, negatives, one item, empty input? | `add(-2, -3) == -5`, `average([7]) == 7` |
| **Error case** | Does bad input fail clearly? | `divide(10, 0)` raises `ValueError` |

### Testing that an error is raised

```python
def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="divide by zero"):
        divide(10, 0)
```

The test **passes** only if `divide(10, 0)` raises a `ValueError` whose message contains "divide by zero". If no error is raised, the test fails. A function that refuses bad input clearly is behaving correctly — test it.

---

## 6 · Floats are approximate: use `pytest.approx`

```python
assert add(0.1, 0.2) == 0.3   # Fails!
```

```text
E       assert 0.30000000000000004 == 0.3
```

Computers store decimals approximately. Compare floats with `pytest.approx`, which allows a tiny difference:

```python
assert add(0.1, 0.2) == pytest.approx(0.3)   # Passes
```

---

## 7 · Parametrize: one test, many cases

Instead of writing four nearly identical tests, list the inputs and expected outputs:

```python
@pytest.mark.parametrize("a, b, expected", [
    (10, 2, 5),
    (9, 3, 3),
    (-8, 2, -4),
    (1, 4, 0.25),
])
def test_divide(a, b, expected):
    assert divide(a, b) == expected
```

pytest runs it four times and reports each one separately:

```text
test_divide[10-2-5] PASSED
test_divide[9-3-3] PASSED
test_divide[-8-2--4] PASSED
test_divide[1-4-0.25] PASSED
```

### Try it: break the code on purpose

In `calculator.py`, change `return a / b` to `return a // b` (integer division). Run the tests:

```text
FAILED test_calculator.py::test_divide[1-4-0.25] - assert 0 == 0.25
========================= 1 failed, 12 passed in 0.02s =========================
```

Only **one** case caught the bug. `10 / 2`, `9 / 3` and `-8 / 2` give whole numbers either way. This is why you pick varied cases, not three versions of the same one. Change it back afterwards.

---

## 8 · Fixtures: fresh setup for every test

`Calculator` remembers its results in `history`. If two tests shared one calculator, the first test's results would leak into the second. A **fixture** builds a fresh one for each test:

```python
@pytest.fixture
def calc():
    return Calculator()

def test_history_records_result(calc):
    calc.add(2, 3)
    assert calc.history == [5]

def test_history_starts_empty(calc):
    assert calc.history == []   # A new Calculator, so history is empty
```

pytest sees the argument name `calc`, runs the fixture with that name, and passes in the result. Tests that don't depend on each other can run in any order and still pass.

---

## 9 · Fakes: don't call slow or paid services in tests

`convert_usd` calls `get_exchange_rate`, which stands in for an online API. Real API calls in tests are slow, cost money, need a network, and return different answers over time. Replace the call with a fixed answer using pytest's built-in `monkeypatch` fixture:

```python
def test_convert_usd_with_fake_rate(monkeypatch):
    monkeypatch.setattr(calculator, "get_exchange_rate", lambda currency: 83.5)
    assert convert_usd(10, "INR") == 835.0
```

The fake lasts only for this one test. This tests **your** logic (multiply and round) without depending on someone else's service. In AI applications the same trick replaces an LLM call with a fixed reply, so you can test the code around the model for free.

---

## 10 · Useful commands

| Command | What it does |
| --- | --- |
| `pytest snippets/pytest_101 -v` | One line per test |
| `pytest snippets/pytest_101 -k divide` | Only tests whose name contains "divide" (`5 passed, 8 deselected`) |
| `pytest snippets/pytest_101 -x` | Stop at the first failure |
| `pytest snippets/pytest_101/test_calculator.py::test_add_floats` | Run one test |

Prefix each with `uv run --with pytest`.

---

## 11 · Kinds of testing

The tests above are **unit tests**. Real projects use several kinds, from small and fast to large and slow:

| Kind | What it checks | Calculator example | Speed |
| --- | --- | --- | --- |
| **Unit test** | One function on its own | `divide(10, 2) == 5` | Milliseconds |
| **Integration test** | Several parts working together | `convert_usd` with a real exchange-rate service | Seconds |
| **End-to-end test** | The whole app, as a user would use it | Type into a calculator web page, read the screen | Seconds to minutes |
| **Regression test** | A bug you fixed stays fixed | After fixing `//`, keep `(1, 4, 0.25)` forever | Same as its kind |

Write many unit tests, fewer integration tests, and a handful of end-to-end tests. Unit tests are fast and point at the exact broken function. The bigger tests catch problems between the parts.

### Where AI applications fit

| What you're testing | Kind of check | Tool |
| --- | --- | --- |
| Your code around the model (parsing, prompts, tool functions) | Exact `assert`, with the LLM faked | pytest + `monkeypatch` |
| The model's answers | Scored against expectations, because the answer can vary | DeepEval metrics inside pytest (`assert_test`) |

An LLM can word the same correct answer differently every run, so `assert answer == "..."` breaks. That's why AI apps add **evaluations**, which score meaning instead of matching text. They still run as pytest tests, so everything in this guide applies.

---

## Checklist: a good test

- [ ] Named `test_...` in a file named `test_...py`
- [ ] Tests one behaviour, and its name says which (`test_divide_by_zero_raises`)
- [ ] Covers the happy path, at least one edge case, and the error case
- [ ] Uses `pytest.approx` for floats
- [ ] Doesn't depend on other tests or their order (use fixtures)
- [ ] Doesn't call real networks or paid APIs (use fakes)
- [ ] You have seen it **fail** once: a test that can't fail proves nothing

**Next:** [Kinds of testing](kinds_of_testing.md): smoke, mock, integration and regression tests, coverage, and flaky tests.
