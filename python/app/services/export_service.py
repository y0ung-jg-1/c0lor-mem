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

    # HDR image export (JPEG/HEIF with gain map)
    if hdr != HdrMode.NONE and fmt in (ExportFormat.PNG, ExportFormat.JPEG, ExportFormat.HEIF):
        filepath = _export_hdr_image(img, request, filename, icc_data)

    # Video export
    elif fmt in (ExportFormat.H264, ExportFormat.H265):
        from app.core.video_encoder import export_video
        filepath = export_video(img, request)

    # Standard SDR image export
    elif fmt == ExportFormat.PNG:
        filepath = os.path.join(request.output_directory, f"{filename}.png")
        img.save(filepath, "PNG", icc_profile=icc_data)

    elif fmt == ExportFormat.JPEG:
        filepath = os.path.join(request.output_directory, f"{filename}.jpg")
        img.save(filepath, "JPEG", quality=98, icc_profile=icc_data)

    elif fmt == ExportFormat.HEIF:
        filepath = os.path.join(request.output_directory, f"{filename}.heic")
        _save_heif(img, filepath, icc_data)

    else:
        filepath = os.path.join(request.output_directory, f"{filename}.png")
        img.save(filepath, "PNG", icc_profile=icc_data)

    file_size = os.path.getsize(filepath)
    return GenerateResponse(output_path=filepath, file_size=file_size)


def _export_hdr_image(
    img: Image.Image,
    request: GenerateRequest,
    filename: str,
    icc_data: bytes | None,
) -> str:
    """Export HDR image with gain map."""
    from app.core.hdr_gainmap import (
        create_apple_gainmap_jpeg,
        create_apple_gainmap_heif,
        create_ultra_hdr_jpeg,
    )

    hdr = request.hdr_mode
    fmt = request.export_format

    if hdr == HdrMode.APPLE_GAINMAP:
        if fmt == ExportFormat.HEIF:
            filepath = os.path.join(request.output_directory, f"{filename}.heic")
            create_apple_gainmap_heif(img, request.hdr_peak_nits, filepath, icc_data)
        else:
            # Default to JPEG for Apple gain map
            filepath = os.path.join(request.output_directory, f"{filename}.jpg")
            create_apple_gainmap_jpeg(img, request.hdr_peak_nits, filepath, icc_data)

    elif hdr == HdrMode.ULTRA_HDR:
        filepath = os.path.join(request.output_directory, f"{filename}.jpg")
        create_ultra_hdr_jpeg(img, request.hdr_peak_nits, filepath, icc_data)

    else:
        # Fallback SDR
        filepath = os.path.join(request.output_directory, f"{filename}.png")
        img.save(filepath, "PNG", icc_profile=icc_data)

    return filepath


def _save_heif(img: Image.Image, filepath: str, icc_data: bytes | None = None) -> None:
    """Save image as HEIF with ICC profile."""
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        raise RuntimeError("pillow-heif is required for HEIF export")

    img.save(filepath, format="HEIF", quality=95)
    if icc_data:
        try:
            from pillow_heif import open_heif
            heif_file = open_heif(filepath)
            heif_file.info["icc_profile"] = icc_data
            heif_file.save(filepath, quality=95)
        except Exception:
            pass
