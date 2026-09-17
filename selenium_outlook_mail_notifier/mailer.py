import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)


from . import exceptions
from .exceptions import ElementNotFoundError

LOGGER = logging.getLogger(__name__)

_TIMEOUT = 10
_STALE_RETRIES = 3


def _wait_and_act(
    driver: webdriver.Chrome,
    by: str,
    value: str,
    action,
    not_found_message: str,
    clickable: bool = False,
) -> None:
    """Wait for an element and run `action` on it, retrying if the element
    goes stale between being located and being acted on (Outlook Web
    re-renders parts of the page as you type/click, which can invalidate a
    just-located element reference -- this isn't a missing selector, just a
    timing race, so it's worth a few retries before giving up).

    For clicks (clickable=True), waits for the element to be visible and
    enabled rather than merely present in the DOM: a button that exists but
    is still disabled while the page validates input can be "clicked"
    without error and without effect, which silently strands the flow on
    the current page instead of raising anything."""
    condition = (
        EC.element_to_be_clickable((by, value))
        if clickable
        else EC.presence_of_element_located((by, value))
    )
    last_exc: Exception | None = None
    for _ in range(_STALE_RETRIES):
        try:
            element: WebElement = WebDriverWait(driver, _TIMEOUT).until(condition)
            action(element)
            return
        except StaleElementReferenceException as exc:
            last_exc = exc
            continue
        except (NoSuchElementException, TimeoutException) as exc:
            driver.quit()
            raise ElementNotFoundError(not_found_message) from exc

    driver.quit()
    raise ElementNotFoundError(f"{not_found_message} (element kept going stale).") from last_exc


def _input_email(driver: webdriver.Chrome, email: str) -> None:
    LOGGER.info("Attempting to input email.")
    _wait_and_act(
        driver, By.ID, "i0116", lambda e: e.send_keys(email),
        "Email input field not found (id='i0116').",
    )
    _wait_and_act(
        driver, By.ID, "idSIButton9", lambda e: e.click(),
        "Next button not found (id='idSIButton9').",
        clickable=True,
    )


def _input_password(driver: webdriver.Chrome, password: str) -> None:
    LOGGER.info("Attempting to input password.")
    _wait_and_act(
        driver, By.ID, "i0118", lambda e: e.send_keys(password),
        "Password input field not found (id='i0118').",
    )
    _wait_and_act(
        driver, By.ID, "idSIButton9", lambda e: e.click(),
        "Sign in button not found (id='idSIButton9').",
        clickable=True,
    )


def _open_new_mail_window(driver: webdriver.Chrome) -> None:
    LOGGER.info("Attempting to open new mail window.")
    _wait_and_act(
        driver, By.XPATH, "//button[@label='New mail']", lambda e: e.click(),
        "New mail button not found (XPATH \"//button[@label='New mail']\").",
        clickable=True,
    )


def _insert_html(element: WebElement, html_body: str) -> None:
    element.parent.execute_script(
        """
        arguments[0].innerHTML = arguments[1];
        arguments[0].dispatchEvent(new InputEvent('input', { bubbles: true }));
        """,
        element,
        html_body,
    )


def _fill_and_send(
    driver: webdriver.Chrome,
    recipient: str,
    subject: str,
    cc: list[str],
    body_text: str | None = None,
    body_html: str | None = None,
) -> None:
    LOGGER.info("Attempting to send email.")
    _wait_and_act(
        driver, By.XPATH, "//div[@aria-label='To']", lambda e: e.send_keys(recipient),
        "Recipient input field not found (XPATH \"//div[@aria-label='To']\").",
    )

    if cc:
        _wait_and_act(
            driver, By.XPATH, "//div[@aria-label='Cc']", lambda e: e.send_keys(";".join(cc)),
            "CC input field not found (XPATH \"//div[@aria-label='Cc']\").",
        )

    _wait_and_act(
        driver, By.XPATH, "//input[@aria-label='Subject']", lambda e: e.send_keys(subject),
        "Subject input field not found (XPATH \"//input[@aria-label='Subject']\").",
    )
    if not body_html and not body_text: body_text = ""
    body_action = (
        (lambda e: _insert_html(e, body_html))
        if body_html is not None
        else (lambda e: e.send_keys(body_text))
    )
    _wait_and_act(
        driver, By.XPATH, "//div[@aria-label='Message body']", body_action,
        "Body input field not found (XPATH \"//div[@aria-label='Message body']\").",
    )

    _wait_and_act(
        driver, By.XPATH, "//button[@aria-label='Send']", lambda e: e.click(),
        "Send button not found (XPATH \"//button[@aria-label='Send']\").",
        clickable=True,
    )


def notify(
    subject: str,
    body: str,
    html_body: bool = False,
    recipient: str | None = None,
    cc: list[str] | None = None,
    sender_email: str | None = None,
    sender_password: str | None = None,
    headless: bool = True,
    enable_logging: bool = True,
) -> None:
    """Log in to Outlook Web via Selenium and send one notification email.

    Credentials/recipient fall back to the OUTLOOK_EMAIL, OUTLOOK_PASSWORD,
    OUTLOOK_RECIPIENT and OUTLOOK_CC environment variables when not passed
    explicitly, so callers never need to hardcode secrets.

    By default, every step (navigating, filling each field, sending) is
    logged, including which selector failed if a step breaks. Pass
    enable_logging=False to silence it for this call.
    """
    sender_email = sender_email or os.environ["OUTLOOK_EMAIL"]
    sender_password = sender_password or os.environ["OUTLOOK_PASSWORD"]
    recipient = recipient or os.environ["OUTLOOK_RECIPIENT"]
    if cc is None:
        cc = [addr for addr in os.environ.get("OUTLOOK_CC", "").split(";") if addr]

    LOGGER.disabled = not enable_logging
    exceptions.LOGGER.disabled = not enable_logging
    try:
        start = time.time()
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        try:
            LOGGER.info("Navigating to Outlook login page...")
            driver.get("https://aka.ms/outlook")

            _input_email(driver, sender_email)
            _input_password(driver, sender_password)

            _open_new_mail_window(driver)
            if html_body:
                _fill_and_send(
                    driver=driver,
                    recipient=recipient,
                    subject=subject,
                    body_html=body,
                    cc=cc
                )
            else:
                _fill_and_send(
                    driver=driver,
                    recipient=recipient,
                    subject=subject,
                    body_text=body,
                    cc=cc
                )
            LOGGER.info("Email probably sent successfully (sent items not checked).")
        finally:
            driver.quit()

        LOGGER.info("notify() completed in %.2f seconds.", time.time() - start)
    finally:
        LOGGER.disabled = False
        exceptions.LOGGER.disabled = False
