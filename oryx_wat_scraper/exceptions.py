"""
Custom exceptions for the Oryx scraper.
"""


class OryxScraperError(Exception):
    """Base exception for all scraper errors."""

    def __init__(self, message: str, status_code: int | None = None):
        """Initialize the exception."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OryxScraperNetworkError(OryxScraperError):
    """Raised when network errors occur."""

    pass


class OryxScraperParseError(OryxScraperError):
    """Raised when HTML parsing fails."""

    pass


class OryxScraperValidationError(OryxScraperError):
    """Raised when data validation fails."""

    pass
