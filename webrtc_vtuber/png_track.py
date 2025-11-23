import asyncio
import logging
import time
from fractions import Fraction
from typing import Optional

import numpy as np
from aiortc import VideoStreamTrack
from av import VideoFrame

from .png_sequence import PngSequence
from .spout_bridge import SpoutBridge

logger = logging.getLogger(__name__)


class PngSequenceVideoTrack(VideoStreamTrack):
    """Loop through a PNG sequence at a configured frame rate."""

    def __init__(
        self,
        sequence: PngSequence,
        fps: int,
        spout: Optional[SpoutBridge] = None,
    ) -> None:
        super().__init__()
        self.sequence = sequence
        self.fps = fps
        self.frame_interval = 1.0 / float(fps)
        self._spout = spout
        self._pts = 0
        self._start = time.perf_counter()

    async def recv(self) -> VideoFrame:
        await asyncio.sleep(self.frame_interval)

        frame_index = int((time.perf_counter() - self._start) * self.fps)
        raw_frame: np.ndarray = self.sequence.frame_at(frame_index)

        if self._spout:
            self._spout.send_frame(raw_frame)

        frame = VideoFrame.from_ndarray(raw_frame, format="rgba")
        frame.pts = self._pts
        frame.time_base = Fraction(1, self.fps)
        self._pts += 1

        logger.debug("Served frame %s (pts=%s)", frame_index, frame.pts)
        return frame
