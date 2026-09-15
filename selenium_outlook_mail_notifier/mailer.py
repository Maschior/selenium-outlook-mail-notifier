import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from .exceptions import ElementNotFoundError

LOGGER = logging.getLogger(__name__)


def _input_email(driver: webdriver.Chrome, email: str) -> None:
    LOGGER.info("Attempting to input email.")
    try:
        driver.find_element("id", "i0116").send_keys(email)
        driver.find_element("id", "idSIButton9").click()
        time.sleep(3)
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "Email input field not found (id='i0116' or button id='idSIButton9')."
        ) from exc


def _input_password(driver: webdriver.Chrome, password: str) -> None:
    LOGGER.info("Attempting to input password.")
    try:
        driver.find_element("id", "i0118").send_keys(password)
        driver.find_element("id", "idSIButton9").click()
        time.sleep(3)
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "Password input field not found (id='i0118' or button id='idSIButton9')."
        ) from exc


def _open_new_mail_window(driver: webdriver.Chrome) -> None:
    LOGGER.info("Attempting to open new mail window.")
    try:
        driver.find_element(By.XPATH, "//button[@label='New mail']").click()
        time.sleep(3)
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "New mail button not found (XPATH \"//button[@label='New mail']\")."
        ) from exc


def _fill_and_send(
    driver: webdriver.Chrome,
    recipient: str,
    subject: str,
    body_text: str,
    cc: list[str],
) -> None:
    LOGGER.info("Attempting to send email.")
    try:
        driver.find_element(By.XPATH, "//div[@aria-label='To']").send_keys(recipient)
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "Recipient input field not found (XPATH \"//div[@aria-label='To']\")."
        ) from exc

    if cc:
        try:
            driver.find_element(By.XPATH, "//div[@aria-label='Cc']").send_keys(";".join(cc))
        except NoSuchElementException as exc:
            driver.quit()
            raise ElementNotFoundError(
                "CC input field not found (XPATH \"//div[@aria-label='Cc']\")."
            ) from exc

    try:
        driver.find_element(By.XPATH, "//input[@aria-label='Subject']").send_keys(subject)
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "Subject input field not found (XPATH \"//input[@aria-label='Subject']\")."
        ) from exc

    try:
        driver.find_element(By.XPATH, "//div[@aria-label='Message body']").send_keys(body_text)
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "Body input field not found (XPATH \"//div[@aria-label='Message body']\")."
        ) from exc

    try:
        driver.find_element(By.XPATH, "//button[@aria-label='Send']").click()
    except NoSuchElementException as exc:
        driver.quit()
        raise ElementNotFoundError(
            "Send button not found (XPATH \"//button[@aria-label='Send']\")."
        ) from exc


def notify(
    subject: str,
    body: str,
    recipient: str | None = None,
    cc: list[str] | None = None,
    sender_email: str | None = None,
    sender_password: str | None = None,
    headless: bool = True,
) -> None:
    """Log in to Outlook Web via Selenium and send one notification email.

    Credentials/recipient fall back to the OUTLOOK_EMAIL, OUTLOOK_PASSWORD,
    OUTLOOK_RECIPIENT and OUTLOOK_CC environment variables when not passed
    explicitly, so callers never need to hardcode secrets.
    """
    sender_email = sender_email or os.environ["OUTLOOK_EMAIL"]
    sender_password = sender_password or os.environ["OUTLOOK_PASSWORD"]
    recipient = recipient or os.environ["OUTLOOK_RECIPIENT"]
    if cc is None:
        cc = [addr for addr in os.environ.get("OUTLOOK_CC", "").split(";") if addr]

    start = time.time()
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    try:
        LOGGER.info("Navigating to Outlook login page...")
        driver.get("https://aka.ms/outlook")
        time.sleep(5)

        _input_email(driver, sender_email)
        _input_password(driver, sender_password)
        time.sleep(5)  # wait for login to complete and the inbox to load

        _open_new_mail_window(driver)
        _fill_and_send(driver, recipient, subject, body, cc)
        time.sleep(5)  # wait for the email to be sent

        LOGGER.info("Email probably sent successfully (sent items not checked).")
    finally:
        driver.quit()

    LOGGER.info("notify() completed in %.2f seconds.", time.time() - start)
