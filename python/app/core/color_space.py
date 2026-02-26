"""
Color space management: ICC profile embedding for exported images.

Supports sRGB (Rec.709), Display P3, and Rec.2020 color spaces.
Generates ICC profiles programmatically.
"""

import os
from PIL import Image
from PIL.ImageCms import ImageCmsProfile, createProfile
from app.core.models import ColorSpace

# Cache for loaded ICC profiles
_icc_cache: dict[str, bytes] = {}


def _build_srgb_profile() -> bytes:
    """Build sRGB ICC profile bytes."""
    profile = createProfile("sRGB")
    return ImageCmsProfile(profile).tobytes()


def _get_icc_profile_path(color_space: ColorSpace) -> str | None:
    """Get path to a bundled ICC profile file, if available."""
    base = os.environ.get("C0LOR_MEM_ICC_DIR", "").strip()
    if not base:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources", "icc-profiles")
    base = os.path.normpath(base)
    mapping = {
        ColorSpace.REC709: "sRGB IEC61966-2.1.icc",
        ColorSpace.DISPLAY_P3: "Display P3.icc",
        ColorSpace.REC2020: "Rec2020.icc",
    }
    filename = mapping.get(color_space)
    if not filename:
        return None
    path = os.path.join(base, filename)
    return path if os.path.exists(path) else None


def _build_profile_for_color_space(color_space: ColorSpace) -> bytes:
    """Build ICC profile for the given color space."""
    if color_space == ColorSpace.REC709:
        return _build_srgb_profile()

    if color_space == ColorSpace.DISPLAY_P3:
        return _create_rgb_profile(
            red_xy=(0.680, 0.320),
            green_xy=(0.265, 0.690),
            blue_xy=(0.150, 0.060),
            white_xy=(0.3127, 0.3290),
            gamma=2.2,
            description="Display P3",
        )

    if color_space == ColorSpace.REC2020:
        return _create_rgb_profile(
            red_xy=(0.708, 0.292),
            green_xy=(0.170, 0.797),
            blue_xy=(0.131, 0.046),
            white_xy=(0.3127, 0.3290),
            gamma=2.2,
            description="Rec. 2020",
        )

    return _build_srgb_profile()


def _create_rgb_profile(
    red_xy: tuple[float, float],
    green_xy: tuple[float, float],
    blue_xy: tuple[float, float],
    white_xy: tuple[float, float],
    gamma: float,
    description: str,
) -> bytes:
    """
    Create a minimal ICC v2 RGB profile with given primaries and gamma.
    Uses struct to build the binary ICC format directly.
    """
    import struct
    import datetime

    def s15f16(val: float) -> bytes:
        """Encode a float as ICC s15Fixed16Number."""
        return struct.pack(">i", round(val * 65536))

    def u16f16(val: float) -> bytes:
        """Encode a float as ICC u16Fixed16Number."""
        return struct.pack(">I", round(val * 65536))

    def xy_to_XYZ(x: float, y: float) -> tuple[float, float, float]:
        """Convert CIE xy chromaticity to XYZ (Y=1)."""
        X = x / y
        Y = 1.0
        Z = (1.0 - x - y) / y
        return (X, Y, Z)

    # Compute colorant XYZ values using chromatic adaptation
    import numpy as np

    white_XYZ = np.array(xy_to_XYZ(*white_xy))
    red_XYZ = np.array(xy_to_XYZ(*red_xy))
    green_XYZ = np.array(xy_to_XYZ(*green_xy))
    blue_XYZ = np.array(xy_to_XYZ(*blue_xy))

    # Build the 3x3 matrix from primaries
    M = np.column_stack([red_XYZ, green_XYZ, blue_XYZ])
    S = np.linalg.solve(M, white_XYZ)

    # Scaled colorants (what goes into ICC rXYZ, gXYZ, bXYZ tags)
    rXYZ = red_XYZ * S[0]
    gXYZ = green_XYZ * S[1]
    bXYZ = blue_XYZ * S[2]

    # Build ICC profile tags
    now = datetime.datetime.now(datetime.timezone.utc)

    # --- Tag: 'desc' ---
    desc_bytes = description.encode("ascii")
    desc_tag = b"desc" + b"\x00" * 4
    desc_tag += struct.pack(">I", len(desc_bytes) + 1)
    desc_tag += desc_bytes + b"\x00"
    # Unicode and ScriptCode placeholders
    desc_tag += b"\x00" * 4  # Unicode language code
    desc_tag += b"\x00" * 4  # Unicode count
    desc_tag += b"\x00" * 2 + b"\x00" + struct.pack(">B", 0) + b"\x00" * 67  # ScriptCode
    # Pad to 4-byte boundary
    while len(desc_tag) % 4:
        desc_tag += b"\x00"

    # --- Tag: 'XYZ ' for colorants and white point ---
    def xyz_tag(X: float, Y: float, Z: float) -> bytes:
        return b"XYZ " + b"\x00" * 4 + s15f16(X) + s15f16(Y) + s15f16(Z)

    wtpt_tag = xyz_tag(*white_XYZ)
    rXYZ_tag = xyz_tag(*rXYZ)
    gXYZ_tag = xyz_tag(*gXYZ)
    bXYZ_tag = xyz_tag(*bXYZ)

    # --- Tag: 'curv' for TRC (simple gamma) ---
    curv_tag = b"curv" + b"\x00" * 4
    curv_tag += struct.pack(">I", 1)  # count = 1 means gamma
    curv_tag += struct.pack(">H", round(gamma * 256))
    curv_tag += b"\x00" * 2  # pad

    # --- Build tag table ---
    tags = {
        b"desc": desc_tag,
        b"wtpt": wtpt_tag,
        b"rXYZ": rXYZ_tag,
        b"gXYZ": gXYZ_tag,
        b"bXYZ": bXYZ_tag,
        b"rTRC": curv_tag,
        b"gTRC": curv_tag,
        b"bTRC": curv_tag,
        b"cprt": desc_tag,  # Reuse desc as copyright
    }

    tag_count = len(tags)
    header_size = 128
    tag_table_size = 4 + tag_count * 12  # count + entries
    data_offset = header_size + tag_table_size

    # Calculate offsets
    tag_entries = []
    tag_data = b""
    offsets_map = {}  # For deduplication (rTRC == gTRC == bTRC)
    for sig, data in tags.items():
        data_id = id(data)
        if data_id in offsets_map:
            # Reuse same offset (deduplicate curv tags)
            tag_entries.append((sig, offsets_map[data_id], len(data)))
        else:
            offset = data_offset + len(tag_data)
            offsets_map[data_id] = offset
            tag_entries.append((sig, offset, len(data)))
            tag_data += data
            # Pad to 4 bytes
            while len(tag_data) % 4:
                tag_data += b"\x00"

    profile_size = data_offset + len(tag_data)

    # --- Build header (128 bytes) ---
    header = struct.pack(">I", profile_size)  # Profile size
    header += b"none"  # Preferred CMM
    header += struct.pack(">I", 0x02400000)  # Version 2.4.0
    header += b"mntr"  # Device class: monitor
    header += b"RGB "  # Color space
    header += b"XYZ "  # PCS
    header += struct.pack(">HHH", now.year, now.month, now.day)
    header += struct.pack(">HHH", now.hour, now.minute, now.second)
    header += b"acsp"  # Profile file signature
    header += b"MSFT"  # Primary platform: Microsoft
    header += b"\x00" * 4  # Profile flags
    header += b"\x00" * 4  # Device manufacturer
    header += b"\x00" * 4  # Device model
    header += b"\x00" * 8  # Device attributes
    header += struct.pack(">I", 0)  # Rendering intent: Perceptual
    header += s15f16(0.9642) + s15f16(1.0) + s15f16(0.8249)  # PCS illuminant D50
    header += b"\x00" * 4  # Profile creator
    header += b"\x00" * 16  # Profile ID
    header += b"\x00" * 28  # Reserved

    assert len(header) == 128

    # --- Build tag table ---
    table = struct.pack(">I", tag_count)
    for sig, offset, size in tag_entries:
        table += sig + struct.pack(">II", offset, size)

    profile_bytes = header + table + tag_data
    assert len(profile_bytes) == profile_size

    return profile_bytes


def get_icc_profile(color_space: ColorSpace) -> bytes:
    """Get ICC profile bytes for the given color space."""
    if color_space in _icc_cache:
        return _icc_cache[color_space]

    # Try bundled file first
    path = _get_icc_profile_path(color_space)
    if path:
        with open(path, "rb") as f:
            data = f.read()
        _icc_cache[color_space] = data
        return data

    # Generate programmatically
    data = _build_profile_for_color_space(color_space)
    _icc_cache[color_space] = data
    return data


def embed_icc_profile(img: Image.Image, color_space: ColorSpace) -> Image.Image:
    """Embed ICC profile into a PIL Image (in-place info update)."""
    icc_data = get_icc_profile(color_space)
    img.info["icc_profile"] = icc_data
    return img
