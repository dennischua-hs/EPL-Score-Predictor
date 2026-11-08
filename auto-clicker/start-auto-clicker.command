#!/bin/bash
# Double-click in Finder to launch the auto clicker (macOS).
# Extra options can be added after auto_clicker.py, e.g. --interval 0.5
cd "$(dirname "$0")" || exit 1
python3 -c "import pynput" 2>/dev/null || { echo "Installing pynput..."; python3 -m pip install --user pynput || exit 1; }
exec python3 auto_clicker.py "$@"
