"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_html():
    """
    Sample Oryx page covering both countries and several categories.

    Mirrors the real page structure: country and category headings are <h3>,
    and each loss line carries one <a> per documented loss.
    """
    return """
    <div class="post-body">
        <h3>Russia - 23933, of which: destroyed: 18606, damaged: 938, abandoned: 1221, captured: 3168</h3>
        <h3>Tanks (4322, of which destroyed: 3225, damaged: 158, abandoned: 400, captured: 539)</h3>
        <p>154 T-62M: <a href="https://example.com/1">(1, destroyed)</a> <a href="https://example.com/2">(2, destroyed)</a> <a href="https://example.com/3">(3, captured)</a></p>
        <p>2 T-54-3M: <a href="https://example.com/4">(1, destroyed)</a></p>
        <h3>Aircraft (137, of which destroyed: 130, damaged: 7)</h3>
        <p>3 Su-34: <a href="https://example.com/5">(1, destroyed)</a> <a href="https://example.com/6">(2, damaged)</a></p>
        <h3>Ukraine - 5000, of which: destroyed: 4000, damaged: 500, abandoned: 200, captured: 300</h3>
        <h3>Tanks (900, of which destroyed: 700, captured: 200)</h3>
        <p>50 T-72AV: <a href="https://example.com/7">(1, captured)</a> <a href="https://example.com/8">(2, abandoned)</a></p>
    </div>
    """


@pytest.fixture
def text_only_html():
    """Sample page whose loss lines carry no links, exercising the text fallback."""
    return """
    <div class="post-body">
        <h3>Russia - 100, of which: destroyed: 100</h3>
        <h3>Tanks (3, of which destroyed: 3)</h3>
        <p>3 T-80U: (1, 2, destroyed) (3, captured)</p>
    </div>
    """
