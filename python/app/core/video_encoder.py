"""
FFmpeg video encoder: generates still-frame videos from test pattern images.

Supports H.264 and H.265 encoding with correct color metadata.
"""

import os
import shutil
import subprocess
import tempfile
from PIL import Image
from app.core.models import GenerateRequest, ExportFormat, ColorSpace, HdrMode


def find_ffmpeg() -> str | None:
    """Find FFmpeg executable path."""
    # Check if ffmpeg is in PATH
    path = shutil.which("ffmpeg")
    if path:
        return path

    # Check common install locations on Windows
    common_paths = [
        os.path.join(os.environ.get("PROGRAMFILES", ""), "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin", "ffmpeg.exe"),
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p

    return None


def _get_color_params(request: GenerateRequest) -> dict[str, str]:
    """Get FFmpeg color metadata parameters based on color space and HDR mode."""
    params: dict[str, str] = {}

    if request.hdr_mode != HdrMode.NONE:
        # HDR: BT.2020 + PQ
        params["colorspace"] = "bt2020nc"
        params["color_primaries"] = "bt2020"
        params["color_trc"] = "smpte2084"  # PQ
        params["pix_fmt"] = "yuv420p10le"  # 10-bit
    elif request.color_space == ColorSpace.REC2020:
        params["colorspace"] = "bt2020nc"
        params["color_primaries"] = "bt2020"
        params["color_trc"] = "bt709"
        params["pix_fmt"] = "yuv420p"
    elif request.color_space == ColorSpace.DISPLAY_P3:
        # P3 doesn't have a native FFmpeg colorspace, use bt709 matrix
        params["colorspace"] = "bt709"
        params["color_primaries"] = "bt709"
        params["color_trc"] = "bt709"
        params["pix_fmt"] = "yuv420p"
    else:
        # Rec.709 / sRGB
        params["colorspace"] = "bt709"
        params["color_primaries"] = "bt709"
        params["color_trc"] = "bt709"
        params["pix_fmt"] = "yuv420p"

    return params


def export_video(img: Image.Image, request: GenerateRequest) -> str:
    """
    Export a still-frame video from a test pattern image.

    Creates a 5-second video at 30fps with the image as every frame.
    """
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. Please install FFmpeg and add it to PATH."
        )

    # Determine codec
    fmt = request.export_format
    if fmt == ExportFormat.H265:
        codec = "libx265"
        ext = ".mp4"
    else:
        codec = "libx264"
        ext = ".mp4"

    color_params = _get_color_params(request)
    pix_fmt = color_params.pop("pix_fmt")

    # Build filename
    parts = [
        f"APL_{request.apl_percent:03d}pct",
        f"{request.width}x{request.height}",
        request.shape.value,
        request.color_space.value,
    ]
    if request.hdr_mode.value != "none":
        parts.append(request.hdr_mode.value)
        parts.append(f"{request.hdr_peak_nits}nits")
    parts.append(codec.replace("lib", ""))
    filename = "_".join(parts) + ext

    output_path = os.path.join(request.output_directory, filename)
    os.makedirs(request.output_directory, exist_ok=True)

    # Save source frame as temporary PNG
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        img.save(tmp_path, "PNG")

    try:
        # Build FFmpeg command
        cmd = [
            ffmpeg_path,
            "-y",  # Overwrite
            "-loop", "1",  # Loop input
            "-i", tmp_path,
            "-c:v", codec,
            "-t", "5",  # 5 seconds
            "-r", "30",  # 30 fps
            "-pix_fmt", pix_fmt,
        ]

        # Add color metadata
        for key, value in color_params.items():
            cmd.extend([f"-{key}", value])

        # Codec-specific options
        if codec == "libx264":
            cmd.extend(["-preset", "medium", "-crf", "18"])
        elif codec == "libx265":
            cmd.extend(["-preset", "medium", "-crf", "20"])
            # x265 params for color metadata
            x265_params = []
            if request.hdr_mode != HdrMode.NONE:
                max_cll = f"{request.hdr_peak_nits},100"
                x265_params.extend([
                    f"max-cll={max_cll}",
                    "hdr-opt=1",
                    "repeat-headers=1",
                ])
            if x265_params:
                cmd.extend(["-x265-params", ":".join(x265_params)])

        cmd.append(output_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")

    finally:
        os.unlink(tmp_path)

    return output_path
