# selenium-outlook-mail-notifier

[![Tests](https://github.com/Maschior/selenium-outlook-mail-notifier/actions/workflows/tests.yml/badge.svg)](https://github.com/Maschior/selenium-outlook-mail-notifier/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/selenium-outlook-mail-notifier.svg)](https://pypi.org/project/selenium-outlook-mail-notifier/)
[![Python versions](https://img.shields.io/pypi/pyversions/selenium-outlook-mail-notifier.svg)](https://pypi.org/project/selenium-outlook-mail-notifier/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
    body="Body message",
    recipient="someone@example.com",  # optional, falls back to OUTLOOK_RECIPIENT
    cc=["other@example.com"],          # optional, falls back to OUTLOOK_CC
    headless=True,                     # optional, defaults to True
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

`notify()` also accepts a `headless` keyword argument (default `True`) that
controls whether Chrome runs headless (`--headless=new`) or with a visible
window, which is useful for debugging selector issues.

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
