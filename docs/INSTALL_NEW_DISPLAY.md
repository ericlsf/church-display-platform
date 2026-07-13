# Install a new Raspberry Pi display

## Raspberry Pi Imager

Use Raspberry Pi OS Desktop 64-bit.

In Imager settings:

- Hostname: choose a unique hostname, such as `church-display-lobby`
- Username: `lsfservice`
- Enable SSH
- Configure Wi-Fi only if Ethernet will not be used
- Set the correct locale and time zone

## Install

After the Pi boots:

```bash
ssh lsfservice@church-display-lobby.local
```

Clone the private repository using SSH:

```bash
git clone git@github.com:ericlsf/church-display-platform.git
cd church-display-platform
git checkout v4.1.0
```

Run:

```bash
./scripts/install-display.sh \
  --hub-url http://church-display-hub.local:8090 \
  --display-name "Lobby Display"
```

Do not run the installer with `sudo`; it requests elevated access only for
system packages and service installation.

## Approve

Open:

```text
http://church-display-hub.local:8090/setup
```

Approve the pending display, then assign its:

- friendly name
- site
- groups
- published playlist

## Verify

```bash
sudo systemctl status church-display-agent.service --no-pager
sudo systemctl status church-display.service --no-pager
sudo journalctl -u church-display-agent.service -n 100 --no-pager
```

After enrollment, normal management should happen from the Hub rather than SSH.
