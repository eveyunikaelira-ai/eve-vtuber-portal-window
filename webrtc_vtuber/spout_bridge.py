import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class SpoutBridge:
    """Lightweight wrapper around Spout2 sender.

    The dependency is optional so that non-Windows platforms can still run the
    WebRTC server without failing imports. When the Spout SDK is unavailable, a
    warning is logged and the send calls are silently ignored.
    """

    def __init__(self, sender_name: str, width: int, height: int) -> None:
        self.sender_name = sender_name
        self.width = width
        self.height = height
        self._sender = self._initialize_sender(sender_name, width, height)

    def _initialize_sender(self, sender_name: str, width: int, height: int):
        try:
            from spout import SpoutSender  # type: ignore
        except ImportError:
            logger.warning(
                "Spout2 SDK is not available. PNG frames will not be published to OBS."
            )
            return None

        sender = SpoutSender(sender_name, width=width, height=height, rgba=True)
        logger.info("Initialized Spout sender '%s' (%sx%s)", sender_name, width, height)
        return sender

    def send_frame(self, frame: np.ndarray) -> None:
        if self._sender is None:
            return

        self._sender.send_image(frame)

    def close(self) -> None:
        if self._sender:
            self._sender.close()
            logger.info("Closed Spout sender '%s'", self.sender_name)
