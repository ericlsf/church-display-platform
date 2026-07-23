# Church Display Platform v13.2.0 — Secure Remote Access

Adds a dedicated Remote Access workspace and production-oriented Cloudflare Tunnel helpers.

## Included
- Remote Access status page and JSON status endpoint.
- Cloudflare Tunnel installation/configuration helper for Debian-based Hub systems.
- Disable/uninstall helper.
- No inbound firewall ports or router port-forwarding are opened.
- Existing Hub authentication remains enabled behind Cloudflare Access.

## Required Cloudflare setup
Create a Cloudflare Access self-hosted application with an Allow policy before publishing the Tunnel hostname. Then create a remotely managed Tunnel route to `http://localhost:8090` and run the command shown on the Remote Access page with its tunnel token.

Tunnel tokens are credentials. Do not paste them into chat, screenshots, tickets, or source control.
