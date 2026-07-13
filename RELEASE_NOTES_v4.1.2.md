# v4.1.2 — Simplified display bootstrap

## Changed

- The Hub-served bootstrap is now intentionally small.
- All operating-system, Python, service, registration, and verification logic
  lives in the maintained `display/install.sh`.
- The display package always includes its installer.
- Shell-script permissions are restored while packaging.
- Missing optional scripts no longer stop installation.
- Interactive installation uses process substitution rather than piping into
  Bash, leaving standard input available for prompts.

## New display command

```bash
bash <(curl -fsSL http://church-display-hub.local:8090/install/display)
```
