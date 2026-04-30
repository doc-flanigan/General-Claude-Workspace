# YouTube Intro

A 6-second animated intro you can drop into the start of your videos.

## Use it

1. Open `intro.html` in a browser (Chrome/Edge recommended for cleanest recording).
2. Click **Edit text** to set your channel name, tagline, and badge.
   - Or pass them via URL: `intro.html?channel=My%20Channel&tagline=Hello&badge=NEW`
3. Press **F11** for fullscreen, then screen-record the window:
   - **OBS**: Window Capture → record at 1080p/60fps.
   - **macOS**: `Cmd+Shift+5` → Record Selected Portion.
   - **Windows**: `Win+G` (Game Bar) → Record.
4. Click **Replay** to re-run the animation.
5. Trim the recording in your video editor and stack it on the front of your videos.

## Customize the look

Edit the `:root` variables at the top of `intro.html`:

| Variable     | What it controls                          |
|--------------|-------------------------------------------|
| `--channel`  | (unused, set via DOM)                     |
| `--accent`   | Primary brand color                       |
| `--accent-2` | Secondary gradient color                  |
| `--bg-1`     | Outer background color                    |
| `--bg-2`     | Inner background glow                     |
| `--duration` | Total intro length (default `6s`)         |

## Animation timeline

- **0.0s** – Background gradients drift in, grid pulses.
- **0.3s** – Badge fades up.
- **0.6s** – Channel name drops in with blur-to-sharp.
- **1.4s** – Tagline fades up.
- **1.9s** – Progress bar fills.
- **4.5s** – White flash transition.
- **6.0s** – Scene zooms out and fades to black.

The flash + fade at the end give you a clean cut into your video's first frame.
