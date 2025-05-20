#!/usr/bin/env python3
"""Overlay a text bubble or bubble GIF onto an MP4 video.

The script can trim the source video, control when the bubble appears
and disappears, and optionally draw a speech bubble using ``drawsvg``.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from typing import Optional, Tuple, Union

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
    output_path: str,
    *,
    text: Optional[str] = None,
    bubble_gif: Optional[str] = None,
    clip_start: float = 0.0,
    clip_end: float | None = None,
    bubble_start: float = 0.0,
    bubble_end: float | None = None,
    position: Union[str, Tuple[int, int]] = "center",
    width: int = 300,
    height: int = 100,
) -> None:
    """Overlay a speech bubble on ``video_path``.

    Either ``text`` or ``bubble_gif`` must be provided.
    """

    if text is None and bubble_gif is None:
        raise ValueError("Provide either text or bubble_gif")

    if bubble_gif:
        bubble_clip = VideoFileClip(bubble_gif).set_start(bubble_start)
    else:
        bubble_png = create_text_bubble(text or "", width, height)
        bubble_clip = ImageClip(bubble_png).set_start(bubble_start)

    video_clip = VideoFileClip(video_path)
    if clip_start != 0.0 or clip_end is not None:
        video_clip = video_clip.subclip(clip_start, clip_end)

    bubble_clip = bubble_clip.set_position(position)
    if bubble_end is not None:
        bubble_clip = bubble_clip.set_end(bubble_end)

    final_clip = CompositeVideoClip([video_clip, bubble_clip])
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    if not bubble_gif:
        os.unlink(bubble_png)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay text bubble onto MP4 video")
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--text", help="Text to display in bubble")
    parser.add_argument("--bubble-gif", help="Use this GIF instead of drawing a bubble")
    parser.add_argument("--clip-start", type=float, default=0.0, help="Start time of the video clip")
    parser.add_argument("--clip-end", type=float, default=None, help="End time of the video clip")
    parser.add_argument("--bubble-start", "--start", dest="bubble_start", type=float, default=0.0, help="Time when the bubble appears")
    parser.add_argument("--bubble-end", "--end", dest="bubble_end", type=float, default=None, help="Time when the bubble disappears")
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
        output_path=args.output,
        text=args.text,
        bubble_gif=args.bubble_gif,
        clip_start=args.clip_start,
        clip_end=args.clip_end,
        bubble_start=args.bubble_start,
        bubble_end=args.bubble_end,
        position=pos,
        width=args.bubble_width,
        height=args.bubble_height,
    )


if __name__ == "__main__":
    main()
