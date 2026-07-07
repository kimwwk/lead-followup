#!/usr/bin/env bash
# open http://localhost:8787/app/
cd "$(dirname "$0")/.."
python3 -m http.server 8787
