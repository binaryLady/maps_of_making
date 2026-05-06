import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "network: mark test as requiring live internet and a running Oxigraph instance")
