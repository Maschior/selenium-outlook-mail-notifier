# Changelog

## Unreleased

- Added optional HTML body support through `notify(..., html_body=True)`,
  while preserving plain-text bodies by default.

## 0.1.3

- `notify()` now requires a recipient (`recipient` argument or
  `OUTLOOK_RECIPIENT` env var) instead of silently falling back to the
  sender's own address.
- Added `headless` argument to `notify()` (default `True`) to run Chrome
  with a visible window for debugging.
- Added `enable_logging` argument to `notify()` (default `True`) to
  silence step-by-step logging for a single call.
- Replaced fixed `time.sleep()` calls with `WebDriverWait`-based explicit
  waits, including waiting for buttons to be clickable (not just present)
  and retrying on stale element references.
- Documented environment variable setup per OS, and the real operational
  constraints of this library (fixed IP/environment, no MFA/CAPTCHA
  support, Outlook Web UI fragility) in the README.

## 0.1.1

- Added Python version and license classifiers to package metadata.

## 0.1.0

- Initial release: `notify()` sends an email through Outlook Web via
  Selenium, with credentials/recipient/CC read from environment variables.
