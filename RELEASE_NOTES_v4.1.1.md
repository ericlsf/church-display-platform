# v4.1.1 — Hub-served display bootstrap

## Added

- Interactive one-command installer served by the Hub.
- Display-only package generated from maintained display source.
- No Git clone or full repository required on displays.
- Automatic Hub inference from the installer URL.
- Prompt for display name and auto-start behavior.
- Automatic enrollment and post-install checks.

## New display command

```bash
curl -fsSL http://church-display-hub.local:8090/install/display | bash
```
