# Shared pytest setup for this folder. Registers the custom markers used in test_kinds_of_testing.py.


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: fast check that the basics work at all")
    config.addinivalue_line("markers", "integration: uses a real external service (slow, may cost money)")
