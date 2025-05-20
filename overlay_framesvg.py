#!/usr/bin/env python3
"""Overlay an animated SVG (converted from a GIF URL) onto an MP4 video.

This script demonstrates how to combine the ``FrameSVG`` library with
``moviepy``.  A GIF is downloaded from a given URL, converted to an
animated SVG using FrameSVG, then rasterised frame by frame so that it
can be composited over a video clip.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from typing import Tuple, Union
from urllib.request import urlretrieve

try:
    import framesvg  # type: ignore
except Exception as exc:  # pragma: no cover - framesvg is optional
    raise ImportError(
        "The FrameSVG package is required for this script."
        " Install it with 'pip install framesvg'."
    ) from exc

try:
    from moviepy.editor import (
        VideoFileClip,
        CompositeVideoClip,
        ImageSequenceClip,
    )
except ImportError as exc:  # pragma: no cover - moviepy is optional
    raise ImportError(
        "The moviepy package is required for this script."
        " Install it with 'pip install moviepy'."
    ) from exc

try:
    import cairosvg  # used to rasterise SVG frames
except Exception as exc:  # pragma: no cover - cairosvg is optional
    raise ImportError(
        "The cairosvg package is required for this script."
        " Install it with 'pip install cairosvg'."
    ) from exc


def gif_url_to_svg(gif_url: str, svg_path: str) -> None:
    """Download ``gif_url`` and convert it to an SVG at ``svg_path``."""
    with tempfile.NamedTemporaryFile(suffix=".gif") as tmp_gif:
        urlretrieve(gif_url, tmp_gif.name)
        framesvg.convert(tmp_gif.name, svg_path)  # type: ignore[attr-defined]


def svg_to_png_frames(svg_path: str, temp_dir: str) -> list[str]:
    """Render an animated SVG to individual PNG frames."""
    sequence = framesvg.FrameSequence.from_svg(svg_path)  # type: ignore[attr-defined]
    png_paths: list[str] = []
    for i, frame in enumerate(sequence.frames):
        png_path = os.path.join(temp_dir, f"frame_{i:04d}.png")
        cairosvg.svg2png(bytestring=frame.to_string().encode(), write_to=png_path)
        png_paths.append(png_path)
    return png_paths


def overlay_svg_on_video(
    video_path: str,
    gif_url: str,
    output_path: str,
    clip_start: float = 0.0,
    clip_end: float | None = None,
    gif_start: float = 0.0,
    gif_end: float | None = None,
    position: Union[str, Tuple[int, int]] = (0, 0),
) -> None:
    """Overlay an animated SVG converted from ``gif_url`` onto ``video_path``."""
    with tempfile.TemporaryDirectory() as tmpdir:
        svg_path = os.path.join(tmpdir, "anim.svg")
        gif_url_to_svg(gif_url, svg_path)
        frame_paths = svg_to_png_frames(svg_path, tmpdir)

        video_clip = VideoFileClip(video_path)
        if clip_start != 0.0 or clip_end is not None:
            video_clip = video_clip.subclip(clip_start, clip_end)

        gif_clip = (
            ImageSequenceClip(frame_paths, fps=len(frame_paths) / max(1, sequence_duration(svg_path)))
            .set_start(gif_start)
            .set_position(position)
        )
        if gif_end is not None:
            gif_clip = gif_clip.set_end(gif_end)

        final_clip = CompositeVideoClip([video_clip, gif_clip])
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")


def sequence_duration(svg_path: str) -> float:
    """Return the duration of an animated SVG created by FrameSVG."""
    seq = framesvg.FrameSequence.from_svg(svg_path)  # type: ignore[attr-defined]
    return seq.duration


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Overlay animated SVG (from GIF URL) onto MP4 video"
    )
    parser.add_argument("--video", required=True, help="Input MP4 video path")
    parser.add_argument("--gif-url", required=True, help="URL of the GIF to convert")
    parser.add_argument("--output", required=True, help="Output MP4 path")
    parser.add_argument("--clip-start", type=float, default=0.0, help="Start time of the video clip")
    parser.add_argument("--clip-end", type=float, default=None, help="End time of the video clip")
    parser.add_argument("--gif-start", "--start", dest="gif_start", type=float, default=0.0, help="Time in seconds when the SVG appears")
    parser.add_argument("--gif-end", type=float, default=None, help="Time in seconds when the SVG disappears")
    parser.add_argument(
        "--position",
        default="center",
        help="Position of SVG: (x,y) or keywords like 'center'",
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

    overlay_svg_on_video(
        video_path=args.video,
        gif_url=args.gif_url,
        output_path=args.output,
        clip_start=args.clip_start,
        clip_end=args.clip_end,
        gif_start=args.gif_start,
        gif_end=args.gif_end,
        position=pos,
    )


if __name__ == "__main__":
    main()
