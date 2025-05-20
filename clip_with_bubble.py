#!/usr/bin/env python3
"""Extract a clip from a video and overlay an SVG speech bubble with text.

This script demonstrates how to use moviepy v2 together with drawsvg to
add simple graphical elements onto a video clip.  It loads the input video,
optionally extracts a subclip, generates an SVG speech bubble containing
text, and overlays that bubble at a specific position and timeframe.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from typing import Tuple, Union

try:
    import drawsvg as draw
except ImportError as exc:  # pragma: no cover - drawsvg is optional
    raise ImportError(
        "The drawsvg package is required for this script."
        " Install it with 'pip install drawsvg'."
    ) from exc

try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
except ImportError as exc:  # pragma: no cover - moviepy is optional
    raise ImportError(
        "The moviepy package is required for this script."
        " Install it with 'pip install moviepy'."
    ) from exc


def create_speech_bubble(text: str, width: int, height: int) -> str:
    """Create an SVG speech bubble with ``text`` and return a temporary PNG path."""
    drawing = draw.Drawing(width, height, origin=(0, 0))

    rect_h = height - 20
    drawing.append(
        draw.Rectangle(
            0,
            0,
            width,
            rect_h,
            rx=15,
            ry=15,
            fill="white",
            stroke="black",
            stroke_width=2,
        )
    )

    drawing.append(
        draw.Lines(
            width * 0.2,
            rect_h,
            width * 0.2 + 20,
            rect_h,
            width * 0.2 + 10,
            height,
            close=True,
            fill="white",
            stroke="black",
            stroke_width=2,
        )
    )

    drawing.append(
        draw.Text(
            text,
            20,
            width / 2,
            rect_h / 2,
            center=True,
            valign="middle",
            fill="black",
        )
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    drawing.save_png(tmp.name)
    return tmp.name


def clip_video_with_bubble(
    video_path: str,
    output_path: str,
    clip_start: float | None,
    clip_end: float | None,
    text: str,
    bubble_start: float,
    bubble_end: float | None,
    position: Union[str, Tuple[int, int]] = "center",
    bubble_width: int = 300,
    bubble_height: int = 100,
) -> None:
    """Extract a clip and overlay a speech bubble on it."""
    bubble_png = create_speech_bubble(text, bubble_width, bubble_height)

    video_clip = VideoFileClip(video_path)
    if clip_start is not None or clip_end is not None:
        video_clip = video_clip.subclip(clip_start or 0, clip_end)

    bubble_clip = ImageClip(bubble_png).set_start(bubble_start).set_position(position)
    if bubble_end is not None:
        bubble_clip = bubble_clip.set_end(bubble_end)

    final_clip = CompositeVideoClip([video_clip, bubble_clip])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    os.unlink(bubble_png)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a video clip and overlay a speech bubble with text"
    )
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument(
        "--clip-start",
        type=float,
        default=None,
        help="Start time of the clip in seconds",
    )
    parser.add_argument(
        "--clip-end",
        type=float,
        default=None,
        help="End time of the clip in seconds",
    )
    parser.add_argument("--text", required=True, help="Text to display in bubble")
    parser.add_argument(
        "--bubble-start",
        type=float,
        default=0.0,
        help="Time when the bubble appears (relative to the clip)",
    )
    parser.add_argument(
        "--bubble-end",
        type=float,
        default=None,
        help="Time when the bubble disappears",
    )
    parser.add_argument(
        "--position",
        default="center",
        help="Position of bubble: (x,y) or keywords like 'center'",
    )
    parser.add_argument(
        "--bubble-width",
        type=int,
        default=300,
        help="Bubble width in pixels",
    )
    parser.add_argument(
        "--bubble-height",
        type=int,
        default=100,
        help="Bubble height in pixels",
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

    clip_video_with_bubble(
        video_path=args.video,
        output_path=args.output,
        clip_start=args.clip_start,
        clip_end=args.clip_end,
        text=args.text,
        bubble_start=args.bubble_start,
        bubble_end=args.bubble_end,
        position=pos,
        bubble_width=args.bubble_width,
        bubble_height=args.bubble_height,
    )


if __name__ == "__main__":
    main()
