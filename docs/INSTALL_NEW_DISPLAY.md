# Install a new Raspberry Pi display

## Image the Pi

Use Raspberry Pi OS Desktop 64-bit.

In Raspberry Pi Imager:

- set a unique hostname;
- create the user `lsfservice`;
- enable SSH;
- configure networking;
- set the correct time zone.

## Run one command

After the Pi boots:

```bash
curl -fsSL http://church-display-hub.local:8090/install/display | bash
```

The guided installer downloads only the player and agent. The display does not
need Git, Hub code, Google Drive credentials, or release-building tools.

## Approve it

Open:

```text
http://church-display-hub.local:8090/setup
```

Approve the pending display, then assign its site, groups, and published playlist.
