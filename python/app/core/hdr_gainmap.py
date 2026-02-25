"""
HDR Gain Map construction for Apple HDR and Ultra HDR formats.

Apple HDR:
  - JPEG: SDR base + gain map in MPF (Multi-Picture Format)
  - HEIF: SDR base + gain map as auxiliary image
  - Gain map JPEG contains XMP with HDRGainMap namespace and apdi:AuxiliaryImageType
  - MakerApple EXIF tags 33 and 48 control HDR rendering behavior

Ultra HDR:
  - ISO 21496-1 based JPEG with gain map
  - Primary image XMP has Container:Directory
  - Gain map JPEG has hdrgm: metadata
  - Compatible with Android HDR display

Gain map calculation:
  - For white pixels: GainMapMax = log2(peak_nits / 203)
  - For black pixels: gain = 0 (no boost)
  - Gain map is grayscale: 0 = no boost, 255 = max boost
"""

import io
import math
import struct
from PIL import Image
from PIL.ExifTags import TAGS
from app.core.models import HdrMode


# Reference SDR white level in nits (sRGB standard)
SDR_WHITE_NITS = 203.0


def _calc_gain_map_max(peak_nits: int) -> float:
    """Calculate the maximum gain map value (log2 scale)."""
    return math.log2(peak_nits / SDR_WHITE_NITS)


def _generate_gain_map(sdr_img: Image.Image, peak_nits: int) -> Image.Image:
    """
    Generate a gain map image from the SDR base.

    White pixels get maximum HDR boost, black pixels get no boost.
    For binary black/white test patterns, the gain map is the luminance channel.
    """
    return sdr_img.convert("L")


def _ensure_rgb(img: Image.Image) -> Image.Image:
    """Ensure image is RGB mode (JPEG doesn't support RGBA)."""
    if img.mode == "RGBA":
        return img.convert("RGB")
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


# ---------------------------------------------------------------------------
# XMP builders (fixed BOM encoding)
# ---------------------------------------------------------------------------

def _build_apple_primary_xmp(peak_nits: int) -> bytes:
    """XMP for the primary (SDR) image in Apple HDR format."""
    headroom = _calc_gain_map_max(peak_nits)
    xmp = (
        "<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>\n"
        "<x:xmpmeta xmlns:x='adobe:ns:meta/'>\n"
        "  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>\n"
        "    <rdf:Description rdf:about=''\n"
        "      xmlns:HDRGainMap='http://ns.apple.com/HDRGainMap/1.0/'\n"
        "      HDRGainMap:HDRGainMapVersion='65536'\n"
        f"      HDRGainMap:HDRGainMapHeadroom='{headroom:.6f}'\n"
        "    />\n"
        "  </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        "<?xpacket end='w'?>"
    )
    return xmp.encode("utf-8")


def _build_apple_gainmap_xmp(peak_nits: int) -> bytes:
    """XMP for the gain map image in Apple HDR format."""
    headroom = _calc_gain_map_max(peak_nits)
    xmp = (
        "<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>\n"
        "<x:xmpmeta xmlns:x='adobe:ns:meta/'>\n"
        "  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>\n"
        "    <rdf:Description rdf:about=''\n"
        "      xmlns:HDRGainMap='http://ns.apple.com/HDRGainMap/1.0/'\n"
        "      xmlns:apdi='http://ns.apple.com/pixeldatainfo/1.0/'\n"
        "      HDRGainMap:HDRGainMapVersion='65536'\n"
        f"      HDRGainMap:HDRGainMapHeadroom='{headroom:.6f}'\n"
        "      apdi:AuxiliaryImageType='urn:com:apple:photo:2020:aux:hdrgainmap'\n"
        "    />\n"
        "  </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        "<?xpacket end='w'?>"
    )
    return xmp.encode("utf-8")


def _build_ultrahdr_primary_xmp(peak_nits: int, gainmap_size: int) -> bytes:
    """XMP for the primary image in Ultra HDR (ISO 21496-1) format."""
    gain_map_max = _calc_gain_map_max(peak_nits)
    xmp = (
        "<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>\n"
        "<x:xmpmeta xmlns:x='adobe:ns:meta/'>\n"
        "  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>\n"
        "    <rdf:Description rdf:about=''\n"
        "      xmlns:hdrgm='http://ns.adobe.com/hdr-gain-map/1.0/'\n"
        "      xmlns:Container='http://ns.google.com/photos/1.0/container/'\n"
        "      xmlns:Item='http://ns.google.com/photos/1.0/container/item/'\n"
        "      hdrgm:Version='1.0'>\n"
        "      <Container:Directory>\n"
        "        <rdf:Seq>\n"
        "          <rdf:li rdf:parseType='Resource'>\n"
        "            <Container:Item Item:Semantic='Primary'"
        " Item:Mime='image/jpeg'/>\n"
        "          </rdf:li>\n"
        "          <rdf:li rdf:parseType='Resource'>\n"
        "            <Container:Item Item:Semantic='GainMap'"
        f" Item:Mime='image/jpeg' Item:Length='{gainmap_size}'/>\n"
        "          </rdf:li>\n"
        "        </rdf:Seq>\n"
        "      </Container:Directory>\n"
        "    </rdf:Description>\n"
        "  </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        "<?xpacket end='w'?>"
    )
    return xmp.encode("utf-8")


def _build_ultrahdr_gainmap_xmp(peak_nits: int) -> bytes:
    """XMP for the gain map image in Ultra HDR (ISO 21496-1) format."""
    gain_map_max = _calc_gain_map_max(peak_nits)
    xmp = (
        "<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>\n"
        "<x:xmpmeta xmlns:x='adobe:ns:meta/'>\n"
        "  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>\n"
        "    <rdf:Description rdf:about=''\n"
        "      xmlns:hdrgm='http://ns.adobe.com/hdr-gain-map/1.0/'\n"
        "      hdrgm:Version='1.0'\n"
        f"      hdrgm:GainMapMin='0.0'\n"
        f"      hdrgm:GainMapMax='{gain_map_max:.6f}'\n"
        "      hdrgm:Gamma='1.0'\n"
        "      hdrgm:OffsetSDR='0.015625'\n"
        "      hdrgm:OffsetHDR='0.015625'\n"
        "      hdrgm:HDRCapacityMin='0.0'\n"
        f"      hdrgm:HDRCapacityMax='{gain_map_max:.6f}'\n"
        "      hdrgm:BaseRenditionIsHDR='False'\n"
        "    />\n"
        "  </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        "<?xpacket end='w'?>"
    )
    return xmp.encode("utf-8")


# ---------------------------------------------------------------------------
# MakerApple EXIF tags builder
# ---------------------------------------------------------------------------

def _build_makerapple_ifd(peak_nits: int) -> bytes:
    """
    Build MakerApple IFD with tags 33 and 48 for HDR rendering control.

    Tag 33: Global brightness boost (0.0-1.0, higher = brighter)
    Tag 48: Gain map contribution (0.0-1.0, lower = more gain map effect)

    Based on toGainMapHDR reference implementation (type II mode).
    Uses fixed values that work reliably across all brightness levels.
    """
    # Use fixed values from toGainMapHDR type II implementation
    # These values enable maximum gain map effect
    tag_33 = 1.01
    tag_48 = 0.009986

    # Build IFD: 2 entries
    ifd = io.BytesIO()
    ifd.write(struct.pack(">H", 2))  # Entry count

    # Tag 33 (0x0021) - FLOAT (11), count=1
    ifd.write(struct.pack(">HHI", 0x0021, 11, 1))
    ifd.write(struct.pack(">f", tag_33))

    # Tag 48 (0x0030) - FLOAT (11), count=1
    ifd.write(struct.pack(">HHI", 0x0030, 11, 1))
    ifd.write(struct.pack(">f", tag_48))

    # Next IFD offset
    ifd.write(struct.pack(">I", 0))

    return ifd.getvalue()


def _inject_makerapple_exif(jpeg_data: bytes, peak_nits: int) -> bytes:
    """
    Inject or update MakerApple tags in EXIF APP1 segment.

    If EXIF exists, append MakerApple IFD. If not, create minimal EXIF.
    """
    assert jpeg_data[:2] == b"\xff\xd8", "Invalid JPEG"

    # Parse existing markers
    pos = 2
    exif_pos = None
    exif_length = 0

    while pos < len(jpeg_data) - 1:
        if jpeg_data[pos] != 0xFF:
            break
        marker = jpeg_data[pos:pos+2]
        if marker == b"\xff\xd9":  # EOI
            break
        if marker == b"\xff\xda":  # SOS (start of scan)
            break
        if marker[1] < 0xD0 or marker[1] > 0xD7:  # Not RSTn
            length = struct.unpack(">H", jpeg_data[pos+2:pos+4])[0]
            if marker == b"\xff\xe1":  # APP1
                # Check if it's EXIF
                if jpeg_data[pos+4:pos+10] == b"Exif\x00\x00":
                    exif_pos = pos
                    exif_length = length
                    break
            pos += 2 + length
        else:
            pos += 2

    makerapple_ifd = _build_makerapple_ifd(peak_nits)

    if exif_pos is None:
        # No EXIF, create minimal EXIF with MakerApple
        # TIFF header + IFD0 with MakerNote pointing to MakerApple IFD
        tiff = io.BytesIO()
        tiff.write(b"MM")  # Big-endian
        tiff.write(b"\x00\x2a")  # TIFF magic
        tiff.write(struct.pack(">I", 8))  # IFD0 offset

        # IFD0: 1 entry (MakerNote)
        tiff.write(struct.pack(">H", 1))
        # Tag 0x927C (MakerNote) - UNDEFINED (7), count=len(makerapple_ifd)
        makerapple_offset = 8 + 2 + 12 + 4  # After IFD0
        tiff.write(struct.pack(">HHI", 0x927C, 7, len(makerapple_ifd)))
        tiff.write(struct.pack(">I", makerapple_offset))
        tiff.write(struct.pack(">I", 0))  # Next IFD

        # Append MakerApple IFD
        tiff.write(b"Apple\x00\x00\x00")  # MakerNote signature
        tiff.write(makerapple_ifd)

        tiff_data = tiff.getvalue()
        exif_payload = b"Exif\x00\x00" + tiff_data
        exif_app1 = b"\xff\xe1" + struct.pack(">H", len(exif_payload) + 2) + exif_payload

        # Insert after SOI
        return jpeg_data[:2] + exif_app1 + jpeg_data[2:]
    else:
        # EXIF exists - this is complex, for now just return original
        # Full implementation would parse TIFF IFD and inject MakerNote
        # For simplicity, we'll skip this and rely on XMP metadata
        return jpeg_data


# ---------------------------------------------------------------------------
# JPEG manipulation helpers
# ---------------------------------------------------------------------------

def _inject_xmp_into_jpeg(jpeg_data: bytes, xmp_bytes: bytes) -> bytes:
    """Inject an XMP APP1 segment into a JPEG right after SOI."""
    assert jpeg_data[:2] == b"\xff\xd8", "Invalid JPEG data"
    xmp_header = b"http://ns.adobe.com/xap/1.0/\x00"
    payload = xmp_header + xmp_bytes
    app1 = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    return jpeg_data[:2] + app1 + jpeg_data[2:]


def _build_mpf_jpeg(
    sdr_jpeg: bytes,
    gainmap_jpeg: bytes,
    primary_xmp: bytes,
    peak_nits: int,
) -> bytes:
    """
    Build an MPF (Multi-Picture Format) JPEG with MakerApple EXIF tags.

    File layout:
      [SOI] [EXIF APP1 with MakerApple] [XMP APP1] [MPF APP2] [rest of primary JPEG] [gain map JPEG]

    MPF offsets are relative to the byte-order mark ("MM") inside the APP2 segment.
    """
    assert sdr_jpeg[:2] == b"\xff\xd8"
    assert gainmap_jpeg[:2] == b"\xff\xd8"

    soi = b"\xff\xd8"
    rest_of_primary = sdr_jpeg[2:]

    # -- EXIF APP1 with MakerApple tags --
    sdr_with_exif = _inject_makerapple_exif(sdr_jpeg, peak_nits)
    exif_app1 = sdr_with_exif[2:] if sdr_with_exif != sdr_jpeg else b""

    # Extract EXIF segment if it was added
    if exif_app1 and exif_app1[:2] == b"\xff\xe1":
        exif_length = struct.unpack(">H", exif_app1[2:4])[0]
        exif_app1 = exif_app1[:2+exif_length]
        rest_of_primary = sdr_jpeg[2:]
    else:
        exif_app1 = b""

    # -- XMP APP1 for primary image --
    xmp_hdr = b"http://ns.adobe.com/xap/1.0/\x00"
    xmp_payload = xmp_hdr + primary_xmp
    xmp_app1 = b"\xff\xe1" + struct.pack(">H", len(xmp_payload) + 2) + xmp_payload

    # -- Build MPF APP2 payload --
    num_ifd_entries = 3
    mp_entry_data_offset = 8 + 2 + num_ifd_entries * 12 + 4  # = 50

    mpf = io.BytesIO()

    # Signature
    mpf.write(b"MPF\x00")

    # TIFF header
    mpf.write(b"MM")             # big-endian (byte-order mark - offset reference point)
    mpf.write(b"\x00\x2a")      # TIFF magic
    mpf.write(struct.pack(">I", 8))  # IFD offset from byte-order

    # IFD
    mpf.write(struct.pack(">H", num_ifd_entries))

    # Tag 0xB000 — MPFVersion (UNDEFINED, 4 bytes, inline value "0100")
    mpf.write(struct.pack(">HHI", 0xB000, 7, 4))
    mpf.write(b"0100")

    # Tag 0xB001 — NumberOfImages (LONG=4, count=1, value=2)
    mpf.write(struct.pack(">HHI", 0xB001, 4, 1))
    mpf.write(struct.pack(">I", 2))

    # Tag 0xB002 — MPEntry (UNDEFINED, 32 bytes, value=offset)
    mpf.write(struct.pack(">HHI", 0xB002, 7, 32))
    mpf.write(struct.pack(">I", mp_entry_data_offset))

    # Next IFD offset
    mpf.write(struct.pack(">I", 0))

    # -- MP Entry 1 (primary image) --
    # Attribute: representative(bit29) + JPEG(000) + Baseline MP Primary(0x030000)
    mpf.write(struct.pack(">I", 0x20030000))
    pos_entry1_size = mpf.tell()
    mpf.write(struct.pack(">I", 0))  # size — placeholder
    mpf.write(struct.pack(">I", 0))  # offset — always 0 for primary
    mpf.write(struct.pack(">HH", 0, 0))

    # -- MP Entry 2 (gain map image) --
    mpf.write(struct.pack(">I", 0x000000))  # Attribute: undefined type
    mpf.write(struct.pack(">I", len(gainmap_jpeg)))  # size
    pos_entry2_offset = mpf.tell()
    mpf.write(struct.pack(">I", 0))  # offset — placeholder
    mpf.write(struct.pack(">HH", 0, 0))

    mpf_bytes = bytearray(mpf.getvalue())

    # -- Calculate actual sizes and offsets --
    mpf_app2 = b"\xff\xe2" + struct.pack(">H", len(mpf_bytes) + 2) + bytes(mpf_bytes)

    primary_total = len(soi) + len(exif_app1) + len(xmp_app1) + len(mpf_app2) + len(rest_of_primary)

    # Byte-order mark position in the file:
    # SOI(2) + exif_app1 + xmp_app1 + FF_E2(2) + length(2) + MPF\0(4) → then "MM"
    bo_pos = len(soi) + len(exif_app1) + len(xmp_app1) + 2 + 2 + 4

    secondary_offset = primary_total - bo_pos

    # Patch placeholders
    struct.pack_into(">I", mpf_bytes, pos_entry1_size, primary_total)
    struct.pack_into(">I", mpf_bytes, pos_entry2_offset, secondary_offset)

    # Rebuild APP2 with patched data
    mpf_app2 = b"\xff\xe2" + struct.pack(">H", len(mpf_bytes) + 2) + bytes(mpf_bytes)

    # -- Assemble --
    out = io.BytesIO()
    out.write(soi)
    if exif_app1:
        out.write(exif_app1)
    out.write(xmp_app1)
    out.write(mpf_app2)
    out.write(rest_of_primary)
    out.write(gainmap_jpeg)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_apple_gainmap_jpeg(
    sdr_img: Image.Image,
    peak_nits: int,
    output_path: str,
    icc_profile: bytes | None = None,
) -> str:
    """
    Create an Apple HDR Gain Map JPEG (MPF format).

    The gain map JPEG carries XMP with HDRGainMap:HDRGainMapVersion and
    apdi:AuxiliaryImageType so macOS/iOS recognise it as HDR.

    Includes MakerApple EXIF tags 33 and 48 for proper HDR rendering.
    """
    sdr_img = _ensure_rgb(sdr_img)
    gain_map = _generate_gain_map(sdr_img, peak_nits)

    # Encode SDR as JPEG
    sdr_buf = io.BytesIO()
    save_kw: dict = {"format": "JPEG", "quality": 98}
    if icc_profile:
        save_kw["icc_profile"] = icc_profile
    sdr_img.save(sdr_buf, **save_kw)
    sdr_jpeg = sdr_buf.getvalue()

    # Encode gain map as JPEG and inject its own XMP
    gm_buf = io.BytesIO()
    gain_map.save(gm_buf, format="JPEG", quality=90)
    gm_jpeg = gm_buf.getvalue()
    gm_xmp = _build_apple_gainmap_xmp(peak_nits)
    gm_jpeg = _inject_xmp_into_jpeg(gm_jpeg, gm_xmp)

    # Primary image XMP
    primary_xmp = _build_apple_primary_xmp(peak_nits)

    # Build MPF with MakerApple EXIF
    mpf_jpeg = _build_mpf_jpeg(sdr_jpeg, gm_jpeg, primary_xmp, peak_nits)

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

    Uses pillow-heif to save with XMP metadata.
    Note: Full gain map auxiliary image requires lower-level HEIF API.
    """
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        raise RuntimeError("pillow-heif required for HEIF HDR export")

    sdr_img = _ensure_rgb(sdr_img)
    xmp_data = _build_apple_primary_xmp(peak_nits)
    sdr_img.info["xmp"] = xmp_data
    if icc_profile:
        sdr_img.info["icc_profile"] = icc_profile

    sdr_img.save(output_path, format="HEIF", quality=95)
    return output_path


def create_ultra_hdr_jpeg(
    sdr_img: Image.Image,
    peak_nits: int,
    output_path: str,
    icc_profile: bytes | None = None,
) -> str:
    """
    Create an Ultra HDR JPEG (ISO 21496-1 / Android compatible).

    Primary image carries Container:Directory XMP; gain map carries
    hdrgm: metadata in its own XMP.
    """
    sdr_img = _ensure_rgb(sdr_img)
    gain_map = _generate_gain_map(sdr_img, peak_nits)

    # Encode SDR as JPEG
    sdr_buf = io.BytesIO()
    save_kw: dict = {"format": "JPEG", "quality": 98}
    if icc_profile:
        save_kw["icc_profile"] = icc_profile
    sdr_img.save(sdr_buf, **save_kw)
    sdr_jpeg = sdr_buf.getvalue()

    # Encode gain map as JPEG and inject its own XMP
    gm_buf = io.BytesIO()
    gain_map.save(gm_buf, format="JPEG", quality=90)
    gm_jpeg = gm_buf.getvalue()
    gm_xmp = _build_ultrahdr_gainmap_xmp(peak_nits)
    gm_jpeg = _inject_xmp_into_jpeg(gm_jpeg, gm_xmp)

    # Primary image XMP (needs gain map JPEG size for Container:Directory)
    primary_xmp = _build_ultrahdr_primary_xmp(peak_nits, len(gm_jpeg))

    # Build MPF (Ultra HDR uses same MPF structure as Apple)
    mpf_jpeg = _build_mpf_jpeg(sdr_jpeg, gm_jpeg, primary_xmp, peak_nits)

    with open(output_path, "wb") as f:
        f.write(mpf_jpeg)
    return output_path
