"""
PQ (SMPTE ST 2084) math and 16-bit PNG writer.

Public functions used by both video_encoder.py and export_service.py.

HDR10 PQ PNG pipeline:
  sRGB pixels → sRGB EOTF → linear light → scale to peak nits
  → PQ OETF → 16-bit numpy array → hand-written 16-bit RGB PNG
  with cICP chunk (BT.2020 + PQ) and optional iCCP profile.
"""

import struct
import zlib
import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# PQ transfer functions
# ---------------------------------------------------------------------------

def srgb_eotf(x: np.ndarray) -> np.ndarray:
    """sRGB EOTF: electrical signal [0, 1] → linear light [0, 1]."""
    return np.where(
        x <= 0.04045,
        x / 12.92,
        np.power((x + 0.055) / 1.055, 2.4),
    )


def pq_oetf(L: np.ndarray) -> np.ndarray:
    """PQ OETF (ST 2084): linear light [0, 1] (1 = 10 000 nits) → PQ signal [0, 1]."""
    m1 = 0.1593017578125   # 2610 / 16384
    m2 = 78.84375          # 2523 / 32
    c1 = 0.8359375         # 3424 / 4096
    c2 = 18.8515625        # 2413 / 128
    c3 = 18.6875           # 2392 / 128
    Lm1 = np.power(np.clip(L, 0.0, 1.0), m1)
    return np.power((c1 + c2 * Lm1) / (1 + c3 * Lm1), m2)


def image_to_pq_rgb48(img: Image.Image, peak_nits: int) -> tuple[bytes, int, int]:
    """
    Convert an sRGB image to PQ-encoded RGB48LE raw frame data.

    Returns (raw_bytes, width, height).
    """
    rgb = img.convert("RGB")
    arr = np.array(rgb).astype(np.float64) / 255.0

    # sRGB → linear light
    linear = srgb_eotf(arr)

    # Scale to absolute luminance, normalise to PQ reference (10 000 nits)
    L = np.clip(linear * (peak_nits / 10000.0), 0.0, 1.0)

    # Linear → PQ signal
    pq = pq_oetf(L)

    # Quantise to 16-bit (numpy native little-endian on x86)
    arr16 = np.clip(pq * 65535.0, 0, 65535).astype(np.uint16)

    h, w = arr16.shape[:2]
    return arr16.tobytes(), w, h


# ---------------------------------------------------------------------------
# 16-bit RGB PNG writer with cICP + iCCP chunks
# ---------------------------------------------------------------------------

def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Build a PNG chunk: length (4 BE) + type (4) + data + CRC32 (4 BE)."""
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return length + chunk_type + data + crc


def _make_cicp_chunk() -> bytes:
    """
    Build a cICP chunk marking BT.2020 primaries + PQ transfer.

    cICP payload (4 bytes):
      colour_primaries   = 9  (BT.2020)
      transfer_function  = 16 (PQ / SMPTE ST 2084)
      matrix_coefficients = 0 (Identity / full-range RGB)
      video_full_range    = 1 (full range)
    """
    data = struct.pack("BBBB", 9, 16, 0, 1)
    return _png_chunk(b"cICP", data)


def _make_iccp_chunk(icc_data: bytes) -> bytes:
    """Build an iCCP chunk embedding the given ICC profile."""
    # iCCP: profile_name (null-terminated) + compression_method (0) + compressed_profile
    profile_name = b"ICC Profile\x00"
    compression_method = b"\x00"
    compressed = zlib.compress(icc_data)
    data = profile_name + compression_method + compressed
    return _png_chunk(b"iCCP", data)


def save_pq_png(
    img: Image.Image,
    peak_nits: int,
    filepath: str,
    icc_data: bytes | None = None,
) -> None:
    """
    Save image as a 16-bit RGB PNG with PQ encoding, cICP chunk, and optional ICC profile.

    Steps:
      1. sRGB → linear → PQ OETF → 16-bit numpy array
      2. Hand-write 16-bit RGB PNG (IHDR bit_depth=16, color_type=2)
      3. Insert cICP chunk (BT.2020 + PQ transfer)
      4. Optionally insert iCCP chunk with ICC profile
    """
    rgb = img.convert("RGB")
    arr = np.array(rgb).astype(np.float64) / 255.0

    # sRGB → linear → PQ
    linear = srgb_eotf(arr)
    L = np.clip(linear * (peak_nits / 10000.0), 0.0, 1.0)
    pq = pq_oetf(L)

    # Quantise to 16-bit big-endian (PNG uses network byte order)
    arr16 = np.clip(pq * 65535.0, 0, 65535).astype(np.uint16)
    h, w = arr16.shape[:2]

    # Build PNG file manually
    png_signature = b"\x89PNG\r\n\x1a\n"

    # IHDR: width(4) height(4) bit_depth(1) color_type(1) compress(1) filter(1) interlace(1)
    ihdr_data = struct.pack(">IIBBBBB", w, h, 16, 2, 0, 0, 0)
    ihdr_chunk = _png_chunk(b"IHDR", ihdr_data)

    # cICP chunk (must appear before IDAT)
    cicp_chunk = _make_cicp_chunk()

    # Optional iCCP chunk
    iccp_chunk = _make_iccp_chunk(icc_data) if icc_data else b""

    # IDAT: scanlines with filter byte 0 (None) per row
    # PNG stores 16-bit values in big-endian
    raw_rows = bytearray()
    for y in range(h):
        raw_rows.append(0)  # filter byte: None
        for x in range(w):
            for c in range(3):
                raw_rows.extend(struct.pack(">H", int(arr16[y, x, c])))

    compressed = zlib.compress(bytes(raw_rows), 9)
    idat_chunk = _png_chunk(b"IDAT", compressed)

    iend_chunk = _png_chunk(b"IEND", b"")

    with open(filepath, "wb") as f:
        f.write(png_signature)
        f.write(ihdr_chunk)
        f.write(cicp_chunk)
        if iccp_chunk:
            f.write(iccp_chunk)
        f.write(idat_chunk)
        f.write(iend_chunk)
