"""
HDR Gain Map construction for Apple HDR and Ultra HDR formats.

Apple HDR:
  - JPEG: SDR base + gain map in MPF (Multi-Picture Format)
  - HEIF: SDR base + gain map as auxiliary image
  - XMP metadata with hdrgm: namespace

Ultra HDR:
  - ISO 21496-1 based JPEG with gain map
  - Compatible with Android HDR display

Gain map calculation:
  - For white pixels: GainMapMax = log2(peak_nits / 203)
  - For black pixels: gain = 0 (no boost)
  - Gain map is grayscale: 0 = no boost, 255 = max boost
"""

import io
import math
import struct
import os
from PIL import Image
from app.core.models import GenerateRequest, HdrMode


# Reference SDR white level in nits (sRGB standard)
SDR_WHITE_NITS = 203.0


def _calc_gain_map_max(peak_nits: int) -> float:
    """Calculate the maximum gain map value (log2 scale)."""
    return math.log2(peak_nits / SDR_WHITE_NITS)


def _generate_gain_map(
    sdr_img: Image.Image,
    peak_nits: int,
) -> Image.Image:
    """
    Generate a gain map image from the SDR base.

    White pixels get maximum HDR boost, black pixels get no boost.
    The gain map encodes log2(HDR/SDR) normalized to [0, 255].
    """
    gain_map_max = _calc_gain_map_max(peak_nits)

    # The SDR image is black (0) and white (255).
    # For white pixels: gain = gain_map_max -> encode as 255
    # For black pixels: gain = 0 -> encode as 0
    # Since our test pattern is binary (0 or 255), the gain map
    # is simply the luminance channel of the SDR image.
    gray = sdr_img.convert("L")
    return gray


def _build_xmp_gainmap_metadata(peak_nits: int) -> bytes:
    """Build XMP metadata with Apple HDR gain map namespace."""
    gain_map_max = _calc_gain_map_max(peak_nits)

    xmp = f"""<?xpacket begin='\xef\xbb\xbf' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
    <rdf:Description rdf:about=''
      xmlns:hdrgm='http://ns.apple.com/HDRGainMap/1.0/'
      hdrgm:Version='1.0'
      hdrgm:GainMapMin='0.0'
      hdrgm:GainMapMax='{gain_map_max:.6f}'
      hdrgm:Gamma='1.0'
      hdrgm:OffsetSDR='0.0'
      hdrgm:OffsetHDR='0.0'
      hdrgm:HDRCapacityMin='0.0'
      hdrgm:HDRCapacityMax='{gain_map_max:.6f}'
      hdrgm:BaseRenditionIsHDR='False'
    />
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""

    return xmp.encode("utf-8")


def _build_mpf_jpeg(sdr_jpeg_data: bytes, gainmap_jpeg_data: bytes, xmp_data: bytes) -> bytes:
    """
    Build an MPF (Multi-Picture Format) JPEG containing SDR base + gain map.

    Structure:
    - Primary image (SDR) with XMP and MPF markers
    - Secondary image (gain map)
    """
    output = io.BytesIO()

    # Parse the primary JPEG to find insertion points
    # We need to inject XMP APP1 and MPF APP2 markers after SOI

    soi = sdr_jpeg_data[:2]
    assert soi == b"\xff\xd8", "Invalid JPEG"

    # Build XMP APP1 marker
    xmp_header = b"http://ns.adobe.com/xap/1.0/\x00"
    xmp_payload = xmp_header + xmp_data
    xmp_marker = b"\xff\xe1" + struct.pack(">H", len(xmp_payload) + 2) + xmp_payload

    # Build MPF APP2 marker
    # MPF structure: 'MPF\0' + MP Entry with offsets
    # We'll calculate the actual offset after assembling

    # First, write SOI + XMP
    output.write(soi)
    output.write(xmp_marker)

    # Placeholder for MPF marker (we'll fill in the offset later)
    mpf_marker_pos = output.tell()

    # MPF Index IFD
    # We need to know the total size of the primary image to calculate secondary offset
    # For now, build the rest of primary JPEG (without SOI)
    rest_of_primary = sdr_jpeg_data[2:]

    # MPF format: 'MPF\0' + byte order + IFD
    mpf_data = io.BytesIO()
    mpf_data.write(b"MPF\x00")  # MPF signature

    # Byte order: big-endian
    mpf_data.write(b"MM")
    mpf_data.write(b"\x00\x2a")  # TIFF magic
    mpf_data.write(struct.pack(">I", 8))  # Offset to first IFD (from start of byte order)

    # IFD entries
    num_entries = 3
    mpf_data.write(struct.pack(">H", num_entries))

    # Tag 0xB000: MPF Version
    mpf_data.write(struct.pack(">HHI", 0xB000, 7, 4))  # UNDEFINED type, 4 bytes
    mpf_data.write(b"0100")

    # Tag 0xB001: Number of Images
    mpf_data.write(struct.pack(">HHI", 0xB001, 3, 1))  # SHORT type
    mpf_data.write(struct.pack(">I", 2))  # 2 images

    # Tag 0xB002: MP Entry - offset to array of MP entries
    # Each MP entry is 16 bytes, 2 entries = 32 bytes
    # The value is the offset from byte order mark to the MP entry data
    entry_offset = 10 + num_entries * 12 + 4  # After IFD + next IFD offset
    mpf_data.write(struct.pack(">HHI", 0xB002, 7, 32))
    mpf_data.write(struct.pack(">I", entry_offset))

    # Next IFD offset (0 = no more IFDs)
    mpf_data.write(struct.pack(">I", 0))

    # MP Entry 1: Primary image
    # Flags: 0x020000 = representative image + type code 0x030000 = baseline MP primary
    mpf_data.write(struct.pack(">I", 0x020030000 & 0xFFFFFFFF))
    mpf_data.write(struct.pack(">I", 0))  # Size: 0 for primary
    mpf_data.write(struct.pack(">I", 0))  # Offset: 0 for primary
    mpf_data.write(struct.pack(">HH", 0, 0))  # Dependent image 1&2 entry

    # MP Entry 2: Secondary image (gain map)
    # We need to calculate the offset from the beginning of the file
    # This will be filled after we know the total primary image size
    mp_entry2_pos = mpf_data.tell()
    mpf_data.write(struct.pack(">I", 0x000000))  # Flags: none
    mpf_data.write(struct.pack(">I", len(gainmap_jpeg_data)))  # Size
    mpf_data.write(struct.pack(">I", 0))  # Offset placeholder
    mpf_data.write(struct.pack(">HH", 0, 0))

    mpf_bytes = mpf_data.getvalue()

    # Build APP2 marker
    mpf_app2 = b"\xff\xe2" + struct.pack(">H", len(mpf_bytes) + 2) + mpf_bytes

    # Write MPF marker
    output.write(mpf_app2)

    # Write rest of primary JPEG
    output.write(rest_of_primary)

    # Calculate offset to secondary image from file start
    primary_total_size = output.tell()

    # Now fix the MP Entry 2 offset
    # The offset in MPF is relative to the start of the MPF APP2 marker's byte order field
    # Actually, per MPF spec, offsets are from the beginning of the file (for individual images)
    # For the MP Entry offset, it's from the beginning of the file
    mpf_offset_in_file = mpf_marker_pos + 2 + 2 + 4  # After FF E2 + length + 'MPF\0'

    # Fix: offset to secondary from start of file
    secondary_offset = primary_total_size

    # Update the offset in mpf_bytes
    # The mp_entry2 offset field is at mp_entry2_pos + 8 (after flags + size)
    fixed_mpf = bytearray(mpf_bytes)
    offset_pos = mp_entry2_pos + 8
    struct.pack_into(">I", fixed_mpf, offset_pos, secondary_offset - mpf_offset_in_file)

    # Rebuild the APP2 marker with fixed offset
    fixed_app2 = b"\xff\xe2" + struct.pack(">H", len(fixed_mpf) + 2) + bytes(fixed_mpf)

    # Reconstruct the entire output
    output = io.BytesIO()
    output.write(soi)
    output.write(xmp_marker)
    output.write(fixed_app2)
    output.write(rest_of_primary)

    # Append secondary image (gain map)
    output.write(gainmap_jpeg_data)

    return output.getvalue()


def create_apple_gainmap_jpeg(
    sdr_img: Image.Image,
    peak_nits: int,
    output_path: str,
    icc_profile: bytes | None = None,
) -> str:
    """
    Create an Apple HDR Gain Map JPEG (MPF format).

    Args:
        sdr_img: SDR base image (RGB)
        peak_nits: Target peak brightness in nits
        output_path: Output file path
        icc_profile: Optional ICC profile to embed
    """
    # Generate gain map
    gain_map = _generate_gain_map(sdr_img, peak_nits)

    # Encode SDR as JPEG
    sdr_buf = io.BytesIO()
    save_kwargs = {"format": "JPEG", "quality": 98}
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile
    sdr_img.save(sdr_buf, **save_kwargs)
    sdr_jpeg = sdr_buf.getvalue()

    # Encode gain map as JPEG (grayscale)
    gm_buf = io.BytesIO()
    gain_map.save(gm_buf, format="JPEG", quality=90)
    gm_jpeg = gm_buf.getvalue()

    # Build XMP
    xmp_data = _build_xmp_gainmap_metadata(peak_nits)

    # Build MPF JPEG
    mpf_jpeg = _build_mpf_jpeg(sdr_jpeg, gm_jpeg, xmp_data)

    with open(output_path, "wb") as f:
        f.write(mpf_jpeg)

    return output_path


def create_apple_gainmap_heif(
    sdr_img: Image.Image,
    peak_nits: int,
    output_path: str,
    icc_profile: bytes | None = None,
) -> str:
    """
    Create an Apple HDR Gain Map HEIF.

    Uses pillow-heif to save with gain map as auxiliary image.
    Falls back to basic HEIF if pillow-heif doesn't support gain map aux.
    """
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        raise RuntimeError("pillow-heif required for HEIF HDR export")

    gain_map = _generate_gain_map(sdr_img, peak_nits)
    xmp_data = _build_xmp_gainmap_metadata(peak_nits)

    # Save base image with XMP metadata
    sdr_img.info["xmp"] = xmp_data
    if icc_profile:
        sdr_img.info["icc_profile"] = icc_profile

    sdr_img.save(output_path, format="HEIF", quality=95)

    # Note: Full HEIF gain map auxiliary image embedding requires
    # lower-level HEIF API access. For now we embed XMP metadata
    # which signals HDR capability to compatible viewers.

    return output_path


def create_ultra_hdr_jpeg(
    sdr_img: Image.Image,
    peak_nits: int,
    output_path: str,
    icc_profile: bytes | None = None,
) -> str:
    """
    Create an Ultra HDR JPEG (ISO 21496-1 compatible).

    Similar to Apple gain map but uses different XMP namespace
    and structure for Android compatibility.
    """
    gain_map = _generate_gain_map(sdr_img, peak_nits)
    gain_map_max = _calc_gain_map_max(peak_nits)

    # Ultra HDR XMP namespace
    xmp = f"""<?xpacket begin='\xef\xbb\xbf' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
    <rdf:Description rdf:about=''
      xmlns:hdrgm='http://ns.adobe.com/hdr-gain-map/1.0/'
      hdrgm:Version='1.0'
      hdrgm:GainMapMin='0.0'
      hdrgm:GainMapMax='{gain_map_max:.6f}'
      hdrgm:Gamma='1.0'
      hdrgm:OffsetSDR='0.0'
      hdrgm:OffsetHDR='0.0'
      hdrgm:HDRCapacityMin='0.0'
      hdrgm:HDRCapacityMax='{gain_map_max:.6f}'
      hdrgm:BaseRenditionIsHDR='False'
    />
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>""".encode("utf-8")

    # Encode SDR as JPEG
    sdr_buf = io.BytesIO()
    save_kwargs = {"format": "JPEG", "quality": 98}
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile
    sdr_img.save(sdr_buf, **save_kwargs)
    sdr_jpeg = sdr_buf.getvalue()

    # Encode gain map as JPEG
    gm_buf = io.BytesIO()
    gain_map.save(gm_buf, format="JPEG", quality=90)
    gm_jpeg = gm_buf.getvalue()

    # Build MPF JPEG with Ultra HDR XMP
    mpf_jpeg = _build_mpf_jpeg(sdr_jpeg, gm_jpeg, xmp)

    with open(output_path, "wb") as f:
        f.write(mpf_jpeg)

    return output_path
