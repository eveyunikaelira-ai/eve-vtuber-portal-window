# eve-vtuber-portal-window

A minimal WebRTC streaming service that replays a transparent PNG sequence (e.g., a VTuber animation) using [`aiortc`](https://github.com/aiortc/aiortc). Each frame is also published to OBS via a Spout2 sender so you can add the animated character as a low-latency source.

## Features
- Streams RGBA PNG frames as a WebRTC video track at a configurable frame rate.
- Replays the sequence in a seamless loop.
- Publishes each frame through Spout2 for direct capture in OBS (using the Spout OBS plugin on Windows).
- Simple HTTP signaling endpoint (`POST /offer`) compatible with common WebRTC tooling.

## Setup
1. Install Python 3.10+ and the build dependencies required by `aiortc` and `av`.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Install the Spout2 Python bindings on Windows. The [Spout Python package](https://github.com/spiraltechnica/Spout-for-Python) exposes `spout.SpoutSender`. Ensure the Spout2 runtime is available and `spout` is importable when running the app.
4. Prepare a directory containing your PNG frames (with transparency) ordered as you want them to play.

## Running the server
```bash
python main.py --png-dir ./frames --fps 30 --spout-name "VTuber-WebRTC" --host 0.0.0.0 --port 8080
```

- `--width` / `--height` can resize every frame to match your canvas.
- `--stun` lets you provide a STUN server for NAT traversal (for example, `--stun stun:stun.l.google.com:19302`).
- The server exposes a health check at `GET /health`.

## WebRTC signaling
Send an SDP offer to `POST /offer` in the following shape:
```json
{"sdp": "v=0...", "type": "offer"}
```
The server responds with the answer SDP, ready to feed into your WebRTC client. Any WebRTC stack that can post an offer and consume an answer will work (e.g., a small JavaScript page, an aiortc-based client, or the `wrtc` Node package).

## Using with OBS (Spout2)
1. Install the [Spout2 OBS plugin](https://github.com/Off-World-Live/obs-spout2-plugin) on Windows.
2. Start the server with `--spout-name` set to a memorable label (default is `VTuber-WebRTC`).
3. In OBS, add a **Spout2 Capture** source and choose the sender name you configured. The VTuber animation should appear with its transparent background preserved.

## Development notes
- Frames are converted to RGBA, and each connection receives its own looping `VideoStreamTrack`.
- If the Spout library is missing, the server still streams WebRTC video; Spout publishing is simply skipped with a warning log.
