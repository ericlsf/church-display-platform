#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p logs config

echo "Hub install complete."
echo "Run with:"
echo "cd ~/church-display-platform/hub && source venv/bin/activate && python app.py"


