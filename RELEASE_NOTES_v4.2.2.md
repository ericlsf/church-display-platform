# v4.2.2 — Safe provisioning and cursor fix

- Replaces the faulty indentation-based patch.
- Removes any prior duplicate or malformed cursor hook.
- Detects the real indentation of `app = QApplication(...)`.
- Inserts exactly one `hide_cursor(app)` call.
- Validates all changed Python modules before completing.
- Retains provisioning readiness and retry support.
