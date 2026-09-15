# selenium-outlook-mail-notifier

Send an email through Outlook Web (outlook.office.com) by driving a real
browser session with Selenium — useful when you don't have Microsoft Graph
API access but still need to trigger email notifications from a script.

## Install

```bash
pip install selenium-outlook-mail-notifier
```

Requires Chrome and a matching chromedriver available on PATH (or managed by
Selenium Manager, which ships with Selenium 4.6+).

## Usage

```python
from selenium_outlook_mail_notifier import notify

notify(
    subject="Something happened",
    body="Triggered by my app's own logic.",
    recipient="someone@example.com",  # optional, falls back to OUTLOOK_RECIPIENT
    cc=["other@example.com"],          # optional, falls back to OUTLOOK_CC
)
```

Credentials are never passed as literals in code. `notify()` reads them from
environment variables unless you pass them explicitly:

| Variable            | Required | Description                          |
|---------------------|----------|---------------------------------------|
| `OUTLOOK_EMAIL`     | yes      | Outlook account used to send the mail |
| `OUTLOOK_PASSWORD`  | yes      | Password for that account             |
| `OUTLOOK_RECIPIENT` | no       | Default recipient if not passed       |
| `OUTLOOK_CC`        | no       | `;`-separated list of CC addresses    |

## License

MIT
