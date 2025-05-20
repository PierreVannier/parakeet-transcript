#!/usr/bin/env python3
"""Overlay an animated GIF onto an MP4 video.

This script uses ``moviepy`` to place a GIF on top of a video at a
specific time and position.

Example usage::

    python overlay_gif.py --video input.mp4 --gif anim.gif \
        --start 5 --position center --output output.mp4

"""

from __future__ import annotations

import argparse
from typing import Tuple, Union

try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip
except ImportError as exc:  # pragma: no cover - moviepy is optional
    raise ImportError(
        "The moviepy package is required for this script."
        " Install it with 'pip install moviepy'."
    ) from exc


def overlay_gif_on_video(
    video_path: str,
    gif_path: str,
    output_path: str,
    start_time: float = 0.0,
    position: Union[str, Tuple[int, int]] = (0, 0),
) -> None:
    """Overlay ``gif_path`` onto ``video_path``.

    Parameters
    ----------
    video_path:
        Path to the input MP4 video.
    gif_path:
        Path to the animated GIF to overlay.
    output_path:
        Where to save the resulting video.
    start_time:
        Time (in seconds) when the GIF should appear.
    position:
        Coordinates or keyword position for the GIF.
    """

    video_clip = VideoFileClip(video_path)
    gif_clip = (
        VideoFileClip(gif_path)
        .set_start(start_time)
        .set_position(position)
    )

    final_clip = CompositeVideoClip([video_clip, gif_clip])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay GIF onto MP4 video")
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--gif", required=True, help="GIF file to overlay")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--start", type=float, default=0.0, help="Time in seconds when the GIF appears")
    parser.add_argument(
        "--position",
        default="center",
        help="Position of GIF: (x,y) or keywords like 'center', 'top', etc.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pos: Union[str, Tuple[int, int]]
    if "," in args.position:
        x_str, y_str = args.position.split(",", maxsplit=1)
        pos = (int(x_str), int(y_str))
    else:
        pos = args.position

    overlay_gif_on_video(
        video_path=args.video,
        gif_path=args.gif,
        output_path=args.output,
        start_time=args.start,
        position=pos,
    )


if __name__ == "__main__":
    main()
