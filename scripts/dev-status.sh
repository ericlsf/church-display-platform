#!/usr/bin/env bash

echo "Processes:"
ps -ef | grep -E "church-display-platform|python -m app.main|python app.py" | grep -v grep || true

echo
echo "Ports:"
ss -ltnp 2>/dev/null | grep -E ":8080|:8090" || true


