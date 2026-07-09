# v1.6.1 - Media Manager Browser

Adds a functional Google Drive media browser in the Hub.

## Added
- Browse Google Drive folders from `/media`.
- Drill into subfolders.
- Optional recursive listing.
- Optional filter to hide unsupported files.
- File cards with image/video/folder icons.
- Playlist statistics: folders, images, videos, supported files, total size.
- One-click set-folder-and-sync job for selected displays.

## Notes
- This version lists remote media through `rclone lsjson`.
- True thumbnails and video duration previews require a future caching/metadata layer.
