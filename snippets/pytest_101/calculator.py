# A tiny calculator: the code under test.


def add(a: float, b: float) -> float:
    return a + b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def average(numbers: list[float]) -> float:
    if not numbers:
        raise ValueError("Cannot average an empty list")
    return sum(numbers) / len(numbers)


class Calculator:
    """Remembers every result, so tests need a fresh one each time."""

    def __init__(self):
        self.history: list[float] = []

    def add(self, a: float, b: float) -> float:
        result = a + b
        self.history.append(result)
        return result


def get_exchange_rate(currency: str) -> float:
    """Pretend this calls a slow, paid, online API (like an LLM call)."""
    raise ConnectionError("No network in tests")


def convert_usd(amount: float, currency: str) -> float:
    return round(amount * get_exchange_rate(currency), 2)
