# v5.7.4 — Stable Upgrade Status Card

## Fixed

Multiple JavaScript controllers were updating the Software card. One controller
could show `Version verified` while another immediately hid or rewrote the
upgrade action.

The individual display page now uses one deployment-status controller.

## Behavior

- `Version verified` remains visible.
- `Manage Versions` always remains available.
- Deploying displays show live progress.
- Failed verification provides a direct review action.
- Legacy verification and timeline scripts are removed from this page to
  prevent competing DOM updates.
