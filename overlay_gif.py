#!/usr/bin/env python3
"""Overlay an animated GIF onto an MP4 video.

This script uses ``moviepy`` to place a GIF on top of a video. It can
optionally trim the input video and control when the GIF appears and
disappears.

Example usage::

    python overlay_gif.py --video input.mp4 --gif anim.gif \
        --gif-start 5 --position center --output output.mp4

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
    clip_start: float = 0.0,
    clip_end: float | None = None,
    gif_start: float = 0.0,
    gif_end: float | None = None,
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
    clip_start:
        Start time of the extracted video clip.
    clip_end:
        End time of the extracted video clip. ``None`` means to use the end of
        the source video.
    gif_start:
        Time (in seconds) when the GIF should appear.
    gif_end:
        Time (in seconds) when the GIF should disappear. ``None`` means to use
        the GIF's full duration.
    position:
        Coordinates or keyword position for the GIF.
    """

    video_clip = VideoFileClip(video_path)
    if clip_start != 0.0 or clip_end is not None:
        video_clip = video_clip.subclip(clip_start, clip_end)

    gif_clip = VideoFileClip(gif_path).set_start(gif_start).set_position(position)
    if gif_end is not None:
        gif_clip = gif_clip.set_end(gif_end)

    final_clip = CompositeVideoClip([video_clip, gif_clip])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay GIF onto MP4 video")
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--gif", required=True, help="GIF file to overlay")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--clip-start", type=float, default=0.0, help="Start time of the video clip")
    parser.add_argument("--clip-end", type=float, default=None, help="End time of the video clip")
    parser.add_argument("--gif-start", "--start", dest="gif_start", type=float, default=0.0, help="Time in seconds when the GIF appears")
    parser.add_argument("--gif-end", type=float, default=None, help="Time in seconds when the GIF disappears")
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
        clip_start=args.clip_start,
        clip_end=args.clip_end,
        gif_start=args.gif_start,
        gif_end=args.gif_end,
        position=pos,
    )


if __name__ == "__main__":
    main()
