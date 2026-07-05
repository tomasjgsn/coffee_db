#!/usr/bin/env bash
# Double-click to stop THE COUNTER's dev server.
cd "$(dirname "${BASH_SOURCE[0]}")/app" && npm run dev:down
echo
read -n 1 -s -r -p "Press any key to close…"
