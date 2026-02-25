"""Export service: handles single image export with format, color space, and HDR options."""

import os
from PIL import Image
from app.core.models import GenerateRequest, GenerateResponse, ExportFormat, HdrMode
from app.core.pattern_generator import generate_pattern_rgba
from app.core.color_space import embed_icc_profile


def _build_filename(request: GenerateRequest) -> str:
    """Build output filename without extension."""
    parts = [
        f"APL_{request.apl_percent:03d}pct",
        f"{request.width}x{request.height}",
        request.shape.value,
        request.color_space.value,
    ]
    if request.hdr_mode.value != "none":
        parts.append(request.hdr_mode.value)
        if request.hdr_mode == HdrMode.HDR10_PQ:
            parts.append(f"{request.hdr_video_peak_nits}nits")
        else:
            parts.append(f"{request.hdr_peak_nits}nits")
    return "_".join(parts)


def export_single(request: GenerateRequest) -> GenerateResponse:
    """Generate and export a single test pattern image."""
    img = generate_pattern_rgba(
        width=request.width,
        height=request.height,
        apl_percent=request.apl_percent,
        shape=request.shape,
    )

    # Embed ICC profile
    embed_icc_profile(img, request.color_space)
    icc_data = img.info.get("icc_profile")

    filename = _build_filename(request)
    os.makedirs(request.output_directory, exist_ok=True)

    fmt = request.export_format
    hdr = request.hdr_mode

    # ---- Video export ----
    if fmt in (ExportFormat.H264, ExportFormat.H265):
        from app.core.video_encoder import export_video
        filepath = export_video(img, request)

    # ---- PNG ----
    elif fmt == ExportFormat.PNG:
        if hdr == HdrMode.HDR10_PQ:
            filepath = _export_pq_png(img, request, filename, icc_data)
        else:
            filepath = os.path.join(request.output_directory, f"{filename}.png")
            img.save(filepath, "PNG", icc_profile=icc_data)

    # ---- JPEG ----
    elif fmt == ExportFormat.JPEG:
        if hdr == HdrMode.ULTRA_HDR:
            filepath = _export_ultra_hdr_jpeg(img, request, filename, icc_data)
        else:
            filepath = os.path.join(request.output_directory, f"{filename}.jpg")
            img.save(filepath, "JPEG", quality=98, icc_profile=icc_data)

    # ---- HEIF ----
    elif fmt == ExportFormat.HEIF:
        # Ultra HDR is JPEG-only; for HEIF just save standard HEIF
        filepath = os.path.join(request.output_directory, f"{filename}.heic")
        _save_heif(img, filepath, icc_data)

    else:
        filepath = os.path.join(request.output_directory, f"{filename}.png")
        img.save(filepath, "PNG", icc_profile=icc_data)

    file_size = os.path.getsize(filepath)
    return GenerateResponse(output_path=filepath, file_size=file_size)


# ---------------------------------------------------------------------------
# HDR image helpers
# ---------------------------------------------------------------------------

def _export_ultra_hdr_jpeg(
    img: Image.Image,
    request: GenerateRequest,
    filename: str,
    icc_data: bytes | None,
) -> str:
    from app.core.hdr_gainmap import create_ultra_hdr_jpeg
    filepath = os.path.join(request.output_directory, f"{filename}.jpg")
    create_ultra_hdr_jpeg(img, request.hdr_peak_nits, filepath, icc_data)
    return filepath


def _export_pq_png(
    img: Image.Image,
    request: GenerateRequest,
    filename: str,
    icc_data: bytes | None,
) -> str:
    from app.core.pq import save_pq_png
    filepath = os.path.join(request.output_directory, f"{filename}.png")
    save_pq_png(img, request.hdr_video_peak_nits, filepath, icc_data)
    return filepath


# ---------------------------------------------------------------------------
# HEIF save helper
# ---------------------------------------------------------------------------

def _save_heif(img: Image.Image, filepath: str, icc_data: bytes | None = None) -> None:
    """Save image as HEIF with ICC profile."""
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        raise RuntimeError("pillow-heif is required for HEIF export")

    save_kw: dict = {"format": "HEIF", "quality": 95}
    if icc_data:
        save_kw["icc_profile"] = icc_data
    img.save(filepath, **save_kw)
