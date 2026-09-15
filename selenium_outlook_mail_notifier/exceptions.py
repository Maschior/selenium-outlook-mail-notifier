import logging

LOGGER = logging.getLogger(__name__)


class ElementNotFoundError(Exception):
    """Raised when a Selenium element is not found in the DOM."""

    def __init__(self, message: str = "Element not found"):
        LOGGER.error(message)
        super().__init__(message)
