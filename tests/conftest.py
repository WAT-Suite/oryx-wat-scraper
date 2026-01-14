"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <div class="post-body">
        <h3>Russia - 23933, of which: destroyed: 18606, damaged: 938, abandoned: 1221, captured: 3168</h3>
        <p>Tanks (4322, of which destroyed: 3225, damaged: 158, abandoned: 400, captured: 539)</p>
        <p>154 T-62M: <a href="https://example.com/1">(1, destroyed)</a> <a href="https://example.com/2">(2, destroyed)</a> <a href="https://example.com/3">(1, captured)</a></p>
        <p>2 T-54-3M: <a href="https://example.com/4">(1, destroyed)</a></p>
    </div>
    """
