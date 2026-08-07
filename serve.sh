#!/usr/bin/env bash
# Build and serve locally. Relative links only resolve over http, not file://
set -e
python3 build.py
echo
echo "→ http://localhost:8000"
python3 -m http.server 8000
