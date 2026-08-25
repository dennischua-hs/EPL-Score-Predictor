#!/bin/bash
# Double-click this file in Finder to launch the EPL Score Predictor.
# It starts the local proxy (if not already running) and opens the app.
# Close this window (or press Ctrl+C) to stop the proxy.

cd "$(dirname "$0")" || exit 1
PORT=8080
URL="http://localhost:$PORT/"

echo "EPL Score Predictor"
echo "-------------------"

# If something is already serving on the port, just open the browser and finish.
if curl -s -o /dev/null --max-time 2 "$URL"; then
  echo "Proxy already running — opening $URL"
  open "$URL"
  echo "(Leave the existing proxy window open. You can close this one.)"
  exit 0
fi

# Otherwise start the proxy, open the browser once it's up, and keep running.
echo "Starting proxy on $URL"
( for i in $(seq 1 20); do
    curl -s -o /dev/null --max-time 1 "$URL" && { open "$URL"; break; }
    sleep 0.5
  done ) &

echo "Keep this window open while you use the app. Press Ctrl+C to stop."
exec python3 proxy.py "$PORT"
