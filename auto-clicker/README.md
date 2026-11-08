# Auto Clicker

A small desktop auto clicker (Python + [pynput](https://pypi.org/project/pynput/)). Works on macOS, Windows and Linux (X11).

## Setup
```bash
pip3 install pynput
```
On **macOS**, the first run will be blocked until you allow your terminal (Terminal / iTerm) in
**System Settings → Privacy & Security → Accessibility** *and* **Input Monitoring**, then restart it.

## Run
```bash
python3 auto_clicker.py            # or double-click start-auto-clicker.command on macOS
```

| Hotkey | Action |
|-------|--------|
| **F6** | Start / pause clicking |
| **F7** | Lock the current mouse position as the target (press again to follow the cursor) |
| **Esc** | Quit |

On Mac laptops you may need **fn + F6 / fn + F7**.

## Options
| Flag | Default | Meaning |
|------|---------|---------|
| `--interval S` | `0.1` | Seconds between clicks |
| `--button left\|right\|middle` | `left` | Mouse button |
| `--clicks N` | `0` (unlimited) | Stop after N clicks |
| `--double` | off | Double-click each time |
| `--jitter S` | `0` | Random ± seconds added to each interval |

Example: `python3 auto_clicker.py --interval 0.5 --clicks 200 --jitter 0.1`

> Use it only where automation is allowed — many games and websites ban auto clickers in their terms.
