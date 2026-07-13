# Troubleshooting

## Hub page shows an error

The error page includes a request reference ID. Search the Hub journal:

```bash
sudo journalctl -u church-display-hub.service --since '10 minutes ago' --no-pager
```

Each response also includes an `X-Request-ID` header.

## Hub is unreachable

```bash
sudo systemctl status church-display-hub.service --no-pager
sudo ss -ltnp | grep :8090
sudo journalctl -u church-display-hub.service -n 100 --no-pager
```

## Agent is online but player is stopped

Use **Start Display App** in the Hub, or run:

```bash
sudo systemctl restart church-display.service
sudo journalctl -u church-display.service -n 100 --no-pager
```

## Content did not update

1. Review Hub content cache and manifest timestamps.
2. Inspect the latest sync job message.
3. Check `display/status/sync.json`.
4. Confirm the sync source is `hub`.
5. Use direct Drive fallback only while diagnosing Hub LAN delivery.

## Validation compiles files inside venv

Use `./scripts/validate-source.sh`. It explicitly skips virtual environments, cache directories, and template-like Python files in dependencies.
