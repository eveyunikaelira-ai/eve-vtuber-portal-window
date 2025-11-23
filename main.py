import argparse
import asyncio
import logging
import pathlib
from typing import List

from aiohttp import web
from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription

from webrtc_vtuber.png_sequence import PngSequence
from webrtc_vtuber.png_track import PngSequenceVideoTrack
from webrtc_vtuber.spout_bridge import SpoutBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webrtc_vtuber")

pcs: List[RTCPeerConnection] = []


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VTuber WebRTC PNG streamer")
    parser.add_argument("--png-dir", type=pathlib.Path, required=True, help="Directory with PNG frames")
    parser.add_argument("--fps", type=int, default=30, help="Playback frame rate")
    parser.add_argument("--width", type=int, default=None, help="Optional resize width")
    parser.add_argument("--height", type=int, default=None, help="Optional resize height")
    parser.add_argument("--spout-name", type=str, default="VTuber-WebRTC", help="Spout2 sender name")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="HTTP host for the signaling server"
    )
    parser.add_argument("--port", type=int, default=8080, help="HTTP port for the signaling server")
    parser.add_argument(
        "--stun", type=str, default=None, help="Optional STUN server URL (e.g. stun:stun.l.google.com:19302)"
    )
    return parser


def create_app(args: argparse.Namespace) -> web.Application:
    target_size = None
    if args.width and args.height:
        target_size = (args.width, args.height)

    sequence = PngSequence(args.png_dir, target_size=target_size)
    logger.info("Prepared %s RGBA frames from %s", len(sequence), args.png_dir)
    first_frame = sequence.frame_at(0)
    spout = SpoutBridge(args.spout_name, first_frame.shape[1], first_frame.shape[0])

    async def offer(request: web.Request) -> web.Response:
        params = await request.json()
        offer_sdp = params.get("sdp")
        offer_type = params.get("type")
        if offer_sdp is None or offer_type is None:
            return web.Response(status=400, text="Invalid offer payload")

        stun_servers = []
        if args.stun:
            stun_servers.append(RTCIceServer(args.stun))
        rtc_config = RTCConfiguration(iceServers=stun_servers)

        pc = RTCPeerConnection(rtc_config)
        pcs.append(pc)
        logger.info("Created peer connection %s", pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info("Connection state changed to %s", pc.connectionState)
            if pc.connectionState in {"failed", "closed"}:
                await pc.close()
                if pc in pcs:
                    pcs.remove(pc)

        track = PngSequenceVideoTrack(sequence=sequence, fps=args.fps, spout=spout)

        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_sdp, type=offer_type))
        pc.addTrack(track)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        logger.info("Answered offer with %s", pc.localDescription.type)
        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})

    async def on_shutdown(app: web.Application) -> None:
        logger.info("Shutting down %s peer connections", len(pcs))
        coros = [pc.close() for pc in pcs]
        await asyncio.gather(*coros, return_exceptions=True)
        pcs.clear()
        spout.close()

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_post("/offer", offer)
    app.router.add_get("/health", lambda _: web.Response(text="ok"))
    return app


def main() -> None:
    parser = create_argument_parser()
    args = parser.parse_args()

    app = create_app(args)
    logger.info("Loaded PNG frames from %s", args.png_dir)
    logger.info("Starting signaling server on %s:%s", args.host, args.port)
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
