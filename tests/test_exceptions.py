import logging

import pytest

from selenium_outlook_mail_notifier import ElementNotFoundError


def test_default_message():
    exc = ElementNotFoundError()
    assert str(exc) == "Element not found"


def test_custom_message():
    exc = ElementNotFoundError("Custom message")
    assert str(exc) == "Custom message"


def test_is_exception():
    assert issubclass(ElementNotFoundError, Exception)


def test_logs_error(caplog):
    with caplog.at_level(logging.ERROR):
        ElementNotFoundError("Boom")
    assert "Boom" in caplog.text


def test_raisable():
    with pytest.raises(ElementNotFoundError, match="oops"):
        raise ElementNotFoundError("oops")
