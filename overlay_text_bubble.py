#!/usr/bin/env python3
"""Overlay a text bubble onto an MP4 video using drawsvg and moviepy."""

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


def create_text_bubble(text: str, width: int, height: int) -> str:
    """Create a speech bubble containing ``text`` and return a PNG path."""
    drawing = draw.Drawing(width, height, origin=(0, 0))

    rect_height = height - 20
    drawing.append(
        draw.Rectangle(
            0,
            0,
            width,
            rect_height,
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
            rect_height,
            width * 0.2 + 20,
            rect_height,
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
            rect_height / 2,
            center=True,
            valign="middle",
            fill="black",
        )
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    drawing.save_png(tmp.name)
    return tmp.name


def overlay_text_bubble_on_video(
    video_path: str,
    text: str,
    output_path: str,
    start: float = 0.0,
    end: float | None = None,
    position: Union[str, Tuple[int, int]] = "center",
    width: int = 300,
    height: int = 100,
) -> None:
    """Overlay a speech bubble on ``video_path``."""
    bubble_png = create_text_bubble(text, width, height)

    video_clip = VideoFileClip(video_path)
    bubble_clip = ImageClip(bubble_png).set_start(start).set_position(position)
    if end is not None:
        bubble_clip = bubble_clip.set_end(end)
    else:
        bubble_clip = bubble_clip.set_duration(video_clip.duration)

    final_clip = CompositeVideoClip([video_clip, bubble_clip])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    os.unlink(bubble_png)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay text bubble onto MP4 video")
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--text", required=True, help="Text to display in bubble")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--start", type=float, default=0.0, help="Time when bubble appears")
    parser.add_argument("--end", type=float, default=None, help="Time when bubble disappears")
    parser.add_argument(
        "--position",
        default="center",
        help="Position of bubble: (x,y) or keywords like 'center', 'top', etc.",
    )
    parser.add_argument("--bubble-width", type=int, default=300, help="Bubble width in pixels")
    parser.add_argument("--bubble-height", type=int, default=100, help="Bubble height in pixels")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pos: Union[str, Tuple[int, int]]
    if "," in args.position:
        x_str, y_str = args.position.split(",", maxsplit=1)
        pos = (int(x_str), int(y_str))
    else:
        pos = args.position

    overlay_text_bubble_on_video(
        video_path=args.video,
        text=args.text,
        output_path=args.output,
        start=args.start,
        end=args.end,
        position=pos,
        width=args.bubble_width,
        height=args.bubble_height,
    )


if __name__ == "__main__":
    main()
