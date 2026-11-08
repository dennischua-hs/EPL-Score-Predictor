#!/usr/bin/env python3
"""
Simple desktop auto clicker.

Hotkeys (work while any app is focused):
  F6   start / pause clicking at the current mouse position
  F7   lock the current mouse position as the click target (press again to unlock)
  Esc  quit

Examples:
  python3 auto_clicker.py                       # 10 clicks/sec, left button, until stopped
  python3 auto_clicker.py --interval 0.5        # one click every half second
  python3 auto_clicker.py --button right --clicks 100
  python3 auto_clicker.py --double --jitter 0.05
"""
import argparse
import random
import sys
import threading
import time

try:
    from pynput import keyboard, mouse
except ImportError:
    sys.exit("Missing dependency: run  pip3 install pynput")

BUTTONS = {"left": mouse.Button.left, "right": mouse.Button.right, "middle": mouse.Button.middle}
KEYS = {
    "toggle": keyboard.Key.f6,
    "lock": keyboard.Key.f7,
    "quit": keyboard.Key.esc,
}


class AutoClicker(threading.Thread):
    def __init__(self, interval, button, max_clicks, double, jitter):
        super().__init__(daemon=True)
        self.interval = interval
        self.button = button
        self.max_clicks = max_clicks  # 0 = unlimited
        self.click_count = 2 if double else 1
        self.jitter = jitter
        self.mouse = mouse.Controller()
        self.target = None  # locked (x, y) or None to follow the cursor
        self.clicks_done = 0
        self._running = threading.Event()
        self._quit = threading.Event()

    # --- controls -----------------------------------------------------
    def toggle(self):
        if self._running.is_set():
            self._running.clear()
            print(f"Paused  ({self.clicks_done} clicks so far)")
        else:
            self._running.set()
            where = f"locked at {self.target}" if self.target else "following cursor"
            print(f"Clicking every {self.interval}s, {where}  (F6 to pause)")

    def toggle_lock(self):
        if self.target:
            self.target = None
            print("Target unlocked — clicking wherever the cursor is")
        else:
            self.target = tuple(int(v) for v in self.mouse.position)
            print(f"Target locked at {self.target}")

    def stop(self):
        self._running.clear()
        self._quit.set()

    # --- loop ---------------------------------------------------------
    def run(self):
        while not self._quit.is_set():
            if not self._running.wait(timeout=0.1):
                continue
            if self.target:
                self.mouse.position = self.target
            self.mouse.click(self.button, self.click_count)
            self.clicks_done += 1
            if self.max_clicks and self.clicks_done >= self.max_clicks:
                print(f"Reached {self.max_clicks} clicks — stopping.")
                self.stop()
                break
            delay = self.interval + random.uniform(-self.jitter, self.jitter)
            # Sleep in a way that reacts quickly to pause/quit.
            self._quit.wait(max(0.001, delay))


def parse_args():
    p = argparse.ArgumentParser(description="Desktop auto clicker (F6 start/pause, F7 lock position, Esc quit)")
    p.add_argument("--interval", type=float, default=0.1, help="seconds between clicks (default 0.1)")
    p.add_argument("--button", choices=BUTTONS, default="left", help="mouse button (default left)")
    p.add_argument("--clicks", type=int, default=0, help="stop after N clicks (default 0 = unlimited)")
    p.add_argument("--double", action="store_true", help="double-click each time")
    p.add_argument("--jitter", type=float, default=0.0, help="random +/- seconds added to each interval")
    a = p.parse_args()
    if a.interval < 0.001:
        p.error("--interval must be at least 0.001")
    if a.jitter < 0 or a.jitter >= a.interval:
        p.error("--jitter must be >= 0 and smaller than --interval")
    if a.clicks < 0:
        p.error("--clicks must be >= 0")
    return a


def main():
    args = parse_args()
    clicker = AutoClicker(args.interval, BUTTONS[args.button], args.clicks, args.double, args.jitter)
    clicker.start()

    def on_press(key):
        if key == KEYS["toggle"]:
            clicker.toggle()
        elif key == KEYS["lock"]:
            clicker.toggle_lock()
        elif key == KEYS["quit"]:
            clicker.stop()
            return False  # stops the listener

    print("Auto clicker ready.  F6 = start/pause   F7 = lock position   Esc = quit")
    with keyboard.Listener(on_press=on_press) as listener:
        while listener.is_alive() and not clicker._quit.is_set():
            listener.join(0.2)
    print(f"Done. Total clicks: {clicker.clicks_done}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
