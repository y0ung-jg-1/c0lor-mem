"""
FFmpeg video encoder: generates still-frame videos from test pattern images.

Supports:
- H.264 (libx264) and H.265 (libx265)
- SDR: sRGB/BT.709 gamma, Display P3, BT.2020
- HDR10: SMPTE ST 2084 (PQ) transfer function, BT.2020, 10-bit
  - Mastering display color volume (SMPTE ST 2086) SEI
  - Content light level info (MaxCLL / MaxFALL) SEI

HDR pipeline:
  sRGB pixels → sRGB EOTF → linear light → scale to peak nits
  → PQ OETF → 16-bit raw → FFmpeg rawvideo pipe → yuv420p10le
"""

import os
import shutil
import subprocess
import tempfile
import numpy as np
from PIL import Image
from app.core.models import GenerateRequest, ExportFormat, ColorSpace, HdrMode
from app.core.pq import image_to_pq_rgb48


def find_ffmpeg() -> str | None:
    """Find FFmpeg executable path."""
    path = shutil.which("ffmpeg")
    if path:
        return path

    common_paths = [
        os.path.join(
            os.environ.get("PROGRAMFILES", ""), "ffmpeg", "bin", "ffmpeg.exe"
        ),
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin", "ffmpeg.exe"
        ),
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p

    return None




# ---------------------------------------------------------------------------
# Mastering display metadata (SMPTE ST 2086)
# ---------------------------------------------------------------------------

# CIE 1931 chromaticity coordinates × 50 000 (CIPA / x265 convention)
_MASTERING_PRIMARIES = {
    "bt2020": {
        "R": (35400, 14600),
        "G": (8500, 39850),
        "B": (6550, 2300),
        "WP": (15635, 16450),
    },
    "p3": {
        "R": (34000, 16000),
        "G": (13250, 34500),
        "B": (7500, 3000),
        "WP": (15635, 16450),
    },
}


def _mastering_display_string(color_space: ColorSpace, peak_nits: int) -> str:
    """
    Build the x265 ``master-display`` parameter (SMPTE ST 2086).

    Format: G(Gx,Gy)B(Bx,By)R(Rx,Ry)WP(Wx,Wy)L(maxLum,minLum)
    - Chromaticity in units of 0.00002
    - Luminance in units of 0.0001 cd/m²
    """
    key = "p3" if color_space == ColorSpace.DISPLAY_P3 else "bt2020"
    p = _MASTERING_PRIMARIES[key]
    max_lum = peak_nits * 10000  # 0.0001 cd/m²
    min_lum = 50                 # 0.005 cd/m²
    return (
        f"G({p['G'][0]},{p['G'][1]})"
        f"B({p['B'][0]},{p['B'][1]})"
        f"R({p['R'][0]},{p['R'][1]})"
        f"WP({p['WP'][0]},{p['WP'][1]})"
        f"L({max_lum},{min_lum})"
    )


# ---------------------------------------------------------------------------
# FFmpeg colour-space flags
# ---------------------------------------------------------------------------

def _get_color_params(request: GenerateRequest) -> dict[str, str]:
    """Get FFmpeg VUI colour metadata flags."""
    if request.hdr_mode != HdrMode.NONE:
        return {
            "colorspace": "bt2020nc",
            "color_primaries": "bt2020",
            "color_trc": "smpte2084",
        }
    if request.color_space == ColorSpace.REC2020:
        return {
            "colorspace": "bt2020nc",
            "color_primaries": "bt2020",
            "color_trc": "bt709",
        }
    if request.color_space == ColorSpace.DISPLAY_P3:
        return {
            "colorspace": "bt709",
            "color_primaries": "smpte432",  # Display P3
            "color_trc": "bt709",
        }
    # sRGB / BT.709
    return {
        "colorspace": "bt709",
        "color_primaries": "bt709",
        "color_trc": "bt709",
    }


# ---------------------------------------------------------------------------
# Export entry point
# ---------------------------------------------------------------------------

def export_video(img: Image.Image, request: GenerateRequest) -> str:
    """Export a 5-second still-frame video from a test pattern image."""
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. Please install FFmpeg and add it to PATH."
        )

    codec = "libx265" if request.export_format == ExportFormat.H265 else "libx264"
    ext = ".mp4"

    # Build output filename
    parts = [
        f"APL_{request.apl_percent:03d}pct",
        f"{request.width}x{request.height}",
        request.shape.value,
        request.color_space.value,
    ]
    if request.hdr_mode != HdrMode.NONE:
        parts.append(request.hdr_mode.value)
        parts.append(f"{request.hdr_video_peak_nits}nits")
    parts.append(codec.replace("lib", ""))
    output_path = os.path.join(request.output_directory, "_".join(parts) + ext)
    os.makedirs(request.output_directory, exist_ok=True)

    color_params = _get_color_params(request)

    if request.hdr_mode != HdrMode.NONE:
        _export_hdr(img, request, ffmpeg_path, codec, color_params, output_path)
    else:
        _export_sdr(img, request, ffmpeg_path, codec, color_params, output_path)

    return output_path


# ---------------------------------------------------------------------------
# SDR export (8-bit, PNG source)
# ---------------------------------------------------------------------------

def _export_sdr(
    img: Image.Image,
    request: GenerateRequest,
    ffmpeg_path: str,
    codec: str,
    color_params: dict[str, str],
    output_path: str,
) -> None:
    """SDR video: 8-bit YUV420P with colour flags."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        img.convert("RGB").save(tmp_path, "PNG")

    try:
        cmd = [
            ffmpeg_path, "-y",
            "-loop", "1",
            "-i", tmp_path,
            "-c:v", codec,
            "-t", "5",
            "-r", "30",
            "-pix_fmt", "yuv420p",
        ]
        for k, v in color_params.items():
            cmd.extend([f"-{k}", v])

        if codec == "libx264":
            cmd.extend(["-preset", "medium", "-crf", "18"])
        else:
            cmd.extend(["-preset", "medium", "-crf", "20"])

        cmd.append(output_path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# HDR10 export (10-bit PQ, raw pipe)
# ---------------------------------------------------------------------------

def _export_hdr(
    img: Image.Image,
    request: GenerateRequest,
    ffmpeg_path: str,
    codec: str,
    color_params: dict[str, str],
    output_path: str,
) -> None:
    """
    HDR10 video: PQ-encoded 10-bit YUV420P with ST 2086 & MaxCLL metadata.

    Pipeline:
      1. Convert sRGB image → PQ-encoded RGB48LE in Python
      2. Pipe raw frames to FFmpeg at 1 fps (FFmpeg duplicates to 30 fps)
      3. FFmpeg converts RGB48 → yuv420p10le and encodes with HDR metadata
    """
    peak = request.hdr_video_peak_nits
    frame_bytes, w, h = image_to_pq_rgb48(img, peak)

    fps_out = 30
    duration = 5
    # Feed 1 fps; FFmpeg duplicates each frame to reach output fps
    fps_in = 1
    num_input_frames = duration * fps_in  # 5 frames

    cmd = [
        ffmpeg_path, "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb48le",
        "-s", f"{w}x{h}",
        "-r", str(fps_in),
        "-i", "pipe:0",
        "-t", str(duration),
        "-r", str(fps_out),
        "-c:v", codec,
        "-pix_fmt", "yuv420p10le",
    ]

    # VUI colour flags
    for k, v in color_params.items():
        cmd.extend([f"-{k}", v])

    # Codec options + HDR10 SEI metadata
    max_fall = max(1, int(request.apl_percent / 100.0 * peak))

    if codec == "libx265":
        master_display = _mastering_display_string(request.color_space, peak)
        # Must pass colour info via x265-params (FFmpeg -color_* flags
        # only set the container, x265 ignores them for VUI/SEI).
        x265_params = ":".join([
            "colorprim=bt2020",
            "transfer=smpte2084",
            "colormatrix=bt2020nc",
            f"master-display={master_display}",
            f"max-cll={peak},{max_fall}",
            "hdr10-opt=1",
            "repeat-headers=1",
        ])
        cmd.extend(["-preset", "medium", "-crf", "20"])
        cmd.extend(["-x265-params", x265_params])
    else:
        # x264: VUI flags only (no SEI HDR10 metadata support)
        cmd.extend(["-preset", "medium", "-crf", "18"])

    cmd.append(output_path)

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(num_input_frames):
            proc.stdin.write(frame_bytes)
        proc.stdin.close()
        _, stderr = proc.communicate(timeout=300)
    except Exception:
        proc.kill()
        raise

    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed: {stderr.decode('utf-8', errors='replace')[-500:]}"
        )
