import pathlib
from typing import List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image


class PngSequence:
    """Load and normalize a directory of PNG frames.

    Frames are converted to RGBA and resized if a target size is provided.
    """

    def __init__(
        self,
        frame_dir: pathlib.Path,
        target_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        if not frame_dir.exists() or not frame_dir.is_dir():
            raise FileNotFoundError(f"Frame directory not found: {frame_dir}")

        self.frame_dir = frame_dir
        self.target_size = target_size
        self.frames = self._load_frames()
        if not self.frames:
            raise ValueError(f"No PNG frames found in {frame_dir}")

    def _load_frames(self) -> List[np.ndarray]:
        png_files: Sequence[pathlib.Path] = sorted(self.frame_dir.glob("*.png"))
        frames: List[np.ndarray] = []

        for png_file in png_files:
            with Image.open(png_file) as img:
                rgba = img.convert("RGBA")
                if self.target_size:
                    rgba = rgba.resize(self.target_size)
                frames.append(np.array(rgba))

        return frames

    def __len__(self) -> int:
        return len(self.frames)

    def frame_at(self, index: int) -> np.ndarray:
        """Return a copy of the indexed frame to protect shared buffers."""
        if not self.frames:
            raise RuntimeError("PNG sequence is empty")

        normalized_index = index % len(self.frames)
        return self.frames[normalized_index].copy()
