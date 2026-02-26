"""
Root conftest.py — configures pytest-asyncio mode for the whole test suite.
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require live services)"
    )
