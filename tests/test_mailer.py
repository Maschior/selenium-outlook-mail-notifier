from itertools import chain, repeat
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from selenium_outlook_mail_notifier import ElementNotFoundError
from selenium_outlook_mail_notifier.mailer import (
    _fill_and_send,
    _input_email,
    _input_password,
    _open_new_mail_window,
    notify,
)


@pytest.fixture
def driver():
    d = MagicMock()
    # EC.element_to_be_clickable() requires is_displayed()/is_enabled() to
    # report truthy; a bare MagicMock() fails that check (it isn't `== True`).
    d.find_element.return_value.is_displayed.return_value = True
    d.find_element.return_value.is_enabled.return_value = True
    return d


def clickable_element() -> MagicMock:
    """A MagicMock that satisfies EC.element_to_be_clickable()."""
    element = MagicMock()
    element.is_displayed.return_value = True
    element.is_enabled.return_value = True
    return element


@pytest.fixture(autouse=True)
def no_sleep():
    with patch("selenium_outlook_mail_notifier.mailer.time.sleep"):
        yield


@pytest.fixture(autouse=True)
def fast_wait(monkeypatch):
    """Force WebDriverWait's timeout to near-zero so tests that simulate a
    missing element hit TimeoutException immediately instead of waiting out
    the real 10s production timeout."""
    import selenium_outlook_mail_notifier.mailer as mailer_module

    real_wait = mailer_module.WebDriverWait

    def fast_wait_factory(driver, timeout, *args, **kwargs):
        return real_wait(driver, 0.01, *args, **kwargs)

    monkeypatch.setattr(mailer_module, "WebDriverWait", fast_wait_factory)


class TestInputEmail:
    def test_sends_email_and_clicks_next(self, driver):
        _input_email(driver, "user@example.com")

        driver.find_element.assert_any_call("id", "i0116")
        driver.find_element.assert_any_call("id", "idSIButton9")
        driver.find_element.return_value.send_keys.assert_called_with("user@example.com")

    def test_missing_field_quits_driver_and_raises(self, driver):
        driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(ElementNotFoundError):
            _input_email(driver, "user@example.com")

        driver.quit.assert_called_once()


class TestInputPassword:
    def test_sends_password_and_clicks_next(self, driver):
        _input_password(driver, "hunter2")

        driver.find_element.assert_any_call("id", "i0118")
        driver.find_element.return_value.send_keys.assert_called_with("hunter2")

    def test_missing_field_quits_driver_and_raises(self, driver):
        driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(ElementNotFoundError):
            _input_password(driver, "hunter2")

        driver.quit.assert_called_once()


class TestOpenNewMailWindow:
    def test_clicks_new_mail_button(self, driver):
        _open_new_mail_window(driver)

        driver.find_element.return_value.click.assert_called_once()

    def test_missing_button_quits_driver_and_raises(self, driver):
        driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(ElementNotFoundError):
            _open_new_mail_window(driver)

        driver.quit.assert_called_once()

    def test_retries_and_recovers_from_a_stale_element(self, driver):
        stale_element = clickable_element()
        stale_element.click.side_effect = StaleElementReferenceException()
        good_element = clickable_element()
        driver.find_element.side_effect = [stale_element, stale_element, good_element]

        _open_new_mail_window(driver)

        good_element.click.assert_called_once()
        driver.quit.assert_not_called()

    def test_gives_up_after_repeated_stale_element_and_raises(self, driver):
        stale_element = clickable_element()
        stale_element.click.side_effect = StaleElementReferenceException()
        driver.find_element.return_value = stale_element

        with pytest.raises(ElementNotFoundError):
            _open_new_mail_window(driver)

        driver.quit.assert_called_once()


class TestFillAndSend:
    def test_fills_all_fields_and_sends(self, driver):
        _fill_and_send(driver, "to@example.com", "Subject", "Body", ["cc@example.com"])

        elements = driver.find_element.return_value
        elements.send_keys.assert_any_call("to@example.com")
        elements.send_keys.assert_any_call("cc@example.com")
        elements.send_keys.assert_any_call("Subject")
        elements.send_keys.assert_any_call("Body")
        elements.click.assert_called_once()

    def test_skips_cc_when_empty(self, driver):
        _fill_and_send(driver, "to@example.com", "Subject", "Body", [])

        calls = [c.args[0] for c in driver.find_element.call_args_list]
        assert "//div[@aria-label='Cc']" not in calls

    def test_missing_recipient_field_quits_driver_and_raises(self, driver):
        driver.find_element.side_effect = NoSuchElementException()

        with pytest.raises(ElementNotFoundError):
            _fill_and_send(driver, "to@example.com", "Subject", "Body", [])

        driver.quit.assert_called_once()

    def test_missing_send_button_quits_driver_and_raises(self, driver):
        ok = MagicMock()
        driver.find_element.side_effect = chain([ok, ok, ok], repeat(NoSuchElementException()))

        with pytest.raises(ElementNotFoundError):
            _fill_and_send(driver, "to@example.com", "Subject", "Body", [])

        driver.quit.assert_called_once()


class TestNotify:
    @pytest.fixture(autouse=True)
    def mocked_chrome(self, driver):
        with patch("selenium_outlook_mail_notifier.mailer.webdriver.Chrome", return_value=driver):
            yield driver

    def test_uses_explicit_credentials_over_env(self, mocked_chrome, monkeypatch):
        monkeypatch.setenv("OUTLOOK_EMAIL", "env@example.com")
        monkeypatch.setenv("OUTLOOK_PASSWORD", "env-pass")

        with patch("selenium_outlook_mail_notifier.mailer._input_email") as input_email, \
                patch("selenium_outlook_mail_notifier.mailer._input_password") as input_password, \
                patch("selenium_outlook_mail_notifier.mailer._open_new_mail_window"), \
                patch("selenium_outlook_mail_notifier.mailer._fill_and_send"):
            notify(
                subject="Subject",
                body="Body",
                recipient="to@example.com",
                sender_email="explicit@example.com",
                sender_password="explicit-pass",
            )

        input_email.assert_called_once_with(mocked_chrome, "explicit@example.com")
        input_password.assert_called_once_with(mocked_chrome, "explicit-pass")

    def test_falls_back_to_env_credentials(self, mocked_chrome, monkeypatch):
        monkeypatch.setenv("OUTLOOK_EMAIL", "env@example.com")
        monkeypatch.setenv("OUTLOOK_PASSWORD", "env-pass")
        monkeypatch.setenv("OUTLOOK_RECIPIENT", "env-recipient@example.com")
        monkeypatch.delenv("OUTLOOK_CC", raising=False)

        with patch("selenium_outlook_mail_notifier.mailer._input_email") as input_email, \
                patch("selenium_outlook_mail_notifier.mailer._input_password") as input_password, \
                patch("selenium_outlook_mail_notifier.mailer._open_new_mail_window"), \
                patch("selenium_outlook_mail_notifier.mailer._fill_and_send") as fill_and_send:
            notify(subject="Subject", body="Body")

        input_email.assert_called_once_with(mocked_chrome, "env@example.com")
        input_password.assert_called_once_with(mocked_chrome, "env-pass")
        fill_and_send.assert_called_once_with(
            mocked_chrome, "env-recipient@example.com", "Subject", "Body", []
        )

    def test_missing_email_env_raises_key_error(self, mocked_chrome, monkeypatch):
        monkeypatch.delenv("OUTLOOK_EMAIL", raising=False)
        monkeypatch.delenv("OUTLOOK_PASSWORD", raising=False)

        with pytest.raises(KeyError):
            notify(subject="Subject", body="Body")

    def test_missing_recipient_env_raises_key_error(self, mocked_chrome, monkeypatch):
        monkeypatch.setenv("OUTLOOK_EMAIL", "env@example.com")
        monkeypatch.setenv("OUTLOOK_PASSWORD", "env-pass")
        monkeypatch.delenv("OUTLOOK_RECIPIENT", raising=False)

        with pytest.raises(KeyError):
            notify(subject="Subject", body="Body")

    def test_parses_cc_from_env(self, mocked_chrome, monkeypatch):
        monkeypatch.setenv("OUTLOOK_EMAIL", "env@example.com")
        monkeypatch.setenv("OUTLOOK_PASSWORD", "env-pass")
        monkeypatch.setenv("OUTLOOK_CC", "a@example.com;b@example.com")

        with patch("selenium_outlook_mail_notifier.mailer._input_email"), \
                patch("selenium_outlook_mail_notifier.mailer._input_password"), \
                patch("selenium_outlook_mail_notifier.mailer._open_new_mail_window"), \
                patch("selenium_outlook_mail_notifier.mailer._fill_and_send") as fill_and_send:
            notify(subject="Subject", body="Body", recipient="to@example.com")

        fill_and_send.assert_called_once_with(
            mocked_chrome, "to@example.com", "Subject", "Body", ["a@example.com", "b@example.com"]
        )

    def test_quits_driver_even_when_step_fails(self, mocked_chrome, monkeypatch):
        monkeypatch.setenv("OUTLOOK_EMAIL", "env@example.com")
        monkeypatch.setenv("OUTLOOK_PASSWORD", "env-pass")

        with patch(
            "selenium_outlook_mail_notifier.mailer._input_email",
            side_effect=ElementNotFoundError("boom"),
        ):
            with pytest.raises(ElementNotFoundError):
                notify(subject="Subject", body="Body", recipient="to@example.com")

        mocked_chrome.quit.assert_called_once()
