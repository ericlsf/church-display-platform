#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

HUB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HUB_DIR))

from services.config import load_hub_settings
from services.media_index import refresh_media_index


def main():
    parser = argparse.ArgumentParser(description="Refresh the Church Display media metadata cache.")
    parser.add_argument("--remote", default="", help="rclone remote name; defaults to hub configuration")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    remote = args.remote or load_hub_settings().get("drive_remote", "gdrive")
    ok, error = refresh_media_index(remote, timeout=args.timeout)
    if not ok:
        print(error, file=sys.stderr)
        return 1
    print(f"Media index refreshed from {remote}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
