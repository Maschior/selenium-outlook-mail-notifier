# selenium-outlook-mail-notifier

[![Tests](https://github.com/Maschior/selenium-outlook-mail-notifier/actions/workflows/tests.yml/badge.svg)](https://github.com/Maschior/selenium-outlook-mail-notifier/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/selenium-outlook-mail-notifier.svg)](https://pypi.org/project/selenium-outlook-mail-notifier/)
[![Python versions](https://img.shields.io/pypi/pyversions/selenium-outlook-mail-notifier.svg)](https://pypi.org/project/selenium-outlook-mail-notifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Send an email through Outlook Web (outlook.office.com) by driving a real
browser session with Selenium — useful when you don't have Microsoft Graph
API access but still need to trigger email notifications from a script.

## Read this before using it in anything that matters

This automates a password-based login to Outlook Web through a real browser.
It is **not** a substitute for Microsoft Graph API and should be treated as
a last resort for environments where Graph access genuinely isn't available
(e.g. you don't have permission to register an app/grant API permissions in
your organization's tenant), not as a general-purpose mailer.

- **It only works reliably from a fixed, known IP/environment.** Microsoft
  treats sign-ins from a new IP or device as suspicious and can trigger
  MFA challenges, "Is this you?" prompts, or account lockouts — none of
  which this library handles. Run it from the same machine/server every
  time, and expect it to break the first time you move it.
- **It does not handle MFA, conditional access, or CAPTCHA at all.** If the
  target account has multi-factor authentication enabled (the default for
  most organizational accounts), `notify()` will fail. This only works
  against accounts with a plain username/password login flow.
- **Outlook Web's UI is not a stable API surface — Microsoft can change
  the page elements this library depends on at any time, without notice.**
  Every selector (`aria-label`, element id) here is scraped from the live
  page as it exists today; a Microsoft UI update can rename or restructure
  any of them and break the corresponding step.
  - By default, `notify()` logs every step it takes (navigating, filling
    each field, sending) and, if a step fails, which selector it was
    looking for when it broke — that's how you find out *which internal
    function* (`_input_email`, `_input_password`, `_open_new_mail_window`,
    or `_fill_and_send`) needs updating. Configure Python's `logging`
    module (e.g. `logging.basicConfig(level=logging.INFO)`) to see it. If
    you don't want that output, pass `enable_logging=False` to `notify()`
    to silence it for that call.
  - If you hit an `ElementNotFoundError`, that's a broken selector, not a
    bug you need to work around yourself — please open a pull request
    (or an issue if you can't fix it) pointing at the failing selector so
    it gets fixed for everyone.
  - Failures still raise `ElementNotFoundError` regardless of the logging
    setting, so a caller can react to them (retry, alert, etc.) even with
    `enable_logging=False`.
- **Passing tests do not mean the live flow works.** The test suite mocks
  the Selenium driver — it verifies the code calls the right selectors in
  the right order, not that Outlook Web's real page still matches those
  selectors. There is no automated end-to-end check against the live
  site (doing so safely in CI, with real credentials and a stable IP,
  isn't practical). Before relying on a new release, do a manual smoke
  test with `headless=False` against a real account.

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
    body="Body message",
    recipient="someone@example.com",  # optional, falls back to OUTLOOK_RECIPIENT
    cc=["other@example.com"],          # optional, falls back to OUTLOOK_CC
    headless=True,                     # optional, defaults to True
    enable_logging=True,               # optional, defaults to True
)
```

Credentials, and the recipient, are never passed as literals in code.
`notify()` reads them from environment variables unless you pass the
corresponding argument explicitly. `sender_email`/`OUTLOOK_EMAIL`,
`sender_password`/`OUTLOOK_PASSWORD` and `recipient`/`OUTLOOK_RECIPIENT`
are all required — one of the two must be provided or `notify()` raises a
`KeyError`.

| Variable            | Required | Description                            |
|---------------------|----------|-----------------------------------------|
| `OUTLOOK_EMAIL`     | yes      | Outlook account used to send the mail   |
| `OUTLOOK_PASSWORD`  | yes      | Password for that account               |
| `OUTLOOK_RECIPIENT` | yes      | Recipient address (if `recipient` isn't passed to `notify()`) |
| `OUTLOOK_CC`        | no       | `;`-separated list of CC addresses      |

`notify()` also accepts:

- `headless` (default `True`): controls whether Chrome runs headless
  (`--headless=new`) or with a visible window, which is useful for
  debugging selector issues.
- `enable_logging` (default `True`): logs every step (see the warning
  above) through Python's standard `logging` module. Pass `False` to
  silence it for that call; failures still raise `ElementNotFoundError`
  either way.

### Setting environment variables

Instead of passing credentials/recipient as arguments, you can set them once
as OS environment variables and let `notify()` pick them up automatically.

#### Windows

Verified on Windows.

**PowerShell** (current session only):

```powershell
$env:OUTLOOK_EMAIL = "you@outlook.com"
$env:OUTLOOK_PASSWORD = "your-password"
$env:OUTLOOK_RECIPIENT = "someone@example.com"
```

**PowerShell** (persist across sessions, current user):

```powershell
[System.Environment]::SetEnvironmentVariable("OUTLOOK_EMAIL", "you@outlook.com", "User")
[System.Environment]::SetEnvironmentVariable("OUTLOOK_PASSWORD", "your-password", "User")
[System.Environment]::SetEnvironmentVariable("OUTLOOK_RECIPIENT", "someone@example.com", "User")
```

Restart your terminal (or IDE) after setting persistent variables so they're
picked up. You can also set them via **Settings > System > About > Advanced
system settings > Environment Variables**.

**cmd.exe** (current session only):

```cmd
set OUTLOOK_EMAIL=you@outlook.com
set OUTLOOK_PASSWORD=your-password
set OUTLOOK_RECIPIENT=someone@example.com
```

#### Linux

> **Not tested by the maintainers** — provided for reference only.

**bash/zsh** (current session only):

```bash
export OUTLOOK_EMAIL="you@outlook.com"
export OUTLOOK_PASSWORD="your-password"
export OUTLOOK_RECIPIENT="someone@example.com"
```

**bash/zsh** (persist across sessions): append the same `export` lines to
`~/.bashrc`, `~/.zshrc`, or `~/.profile`, then run `source` on that file (or
open a new terminal).

#### macOS

> **Not tested by the maintainers** — provided for reference only.

Same as Linux — macOS's default shell (zsh) uses the same `export` syntax:

```bash
export OUTLOOK_EMAIL="you@outlook.com"
export OUTLOOK_PASSWORD="your-password"
export OUTLOOK_RECIPIENT="someone@example.com"
```

Add the `export` lines to `~/.zshrc` (or `~/.bash_profile` if you use bash)
to persist them across sessions.

## Development

```bash
pip install -e ".[test]"
pytest
```
