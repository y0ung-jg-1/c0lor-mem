"""
Ultra HDR (ISO 21496-1) JPEG construction.

Ultra HDR:
  - ISO 21496-1 based JPEG with gain map via MPF (Multi-Picture Format)
  - Primary image XMP has Container:Directory pointing to gain map
  - Gain map JPEG has hdrgm: metadata (version, min/max, gamma, offsets, capacity)
  - Compatible with Android HDR display pipeline

Gain map calculation:
  - For white pixels: GainMapMax = log2(peak_nits / 203)
  - For black pixels: gain = 0 (no boost)
  - Gain map is grayscale: 0 = no boost, 255 = max boost
"""

import io
import math
import struct
from PIL import Image

# Reference SDR white level in nits (sRGB standard)
SDR_WHITE_NITS = 203.0

# Gain map downscale factor (1/4 resolution)
GAINMAP_SCALE = 4


def _calc_gain_map_max(peak_nits: int) -> float:
    """Calculate the maximum gain map value (log2 scale)."""
    return math.log2(peak_nits / SDR_WHITE_NITS)


def _generate_gain_map(sdr_img: Image.Image, peak_nits: int) -> Image.Image:
    """
    Generate a gain map image from the SDR base.

    White pixels get maximum HDR boost, black pixels get no boost.
    For binary black/white test patterns, the gain map is the luminance channel.
    Downsampled to 1/4 resolution to reduce file size.
    """
    gm = sdr_img.convert("L")
    w, h = gm.size
    gm = gm.resize((w // GAINMAP_SCALE, h // GAINMAP_SCALE), Image.LANCZOS)
    return gm


def _ensure_rgb(img: Image.Image) -> Image.Image:
    """Ensure image is RGB mode (JPEG doesn't support RGBA)."""
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


# ---------------------------------------------------------------------------
# XMP builders
# ---------------------------------------------------------------------------

def _build_primary_xmp(peak_nits: int, gainmap_size: int) -> bytes:
    """XMP for the primary image in Ultra HDR (ISO 21496-1) format."""
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


def _build_gainmap_xmp(peak_nits: int) -> bytes:
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
# JPEG / MPF helpers
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
) -> bytes:
    """
    Build an MPF (Multi-Picture Format) JPEG for Ultra HDR.

    File layout:
      [SOI] [XMP APP1] [MPF APP2] [rest of primary JPEG] [gain map JPEG]

    MPF offsets are relative to the byte-order mark ("MM") inside the APP2.
    """
    assert sdr_jpeg[:2] == b"\xff\xd8"
    assert gainmap_jpeg[:2] == b"\xff\xd8"

    soi = b"\xff\xd8"
    rest_of_primary = sdr_jpeg[2:]

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
    mpf.write(b"MM")             # big-endian (byte-order mark - offset reference)
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

    primary_size = len(soi) + len(xmp_app1) + len(mpf_app2) + len(rest_of_primary)

    # Byte-order mark position in the file:
    # SOI(2) + xmp_app1 + FF_E2(2) + length(2) + MPF\0(4) → then "MM"
    bo_pos = len(soi) + len(xmp_app1) + 2 + 2 + 4

    secondary_offset = primary_size - bo_pos

    # Patch placeholders
    struct.pack_into(">I", mpf_bytes, pos_entry1_size, primary_size)
    struct.pack_into(">I", mpf_bytes, pos_entry2_offset, secondary_offset)

    # Rebuild APP2 with patched data
    mpf_app2 = b"\xff\xe2" + struct.pack(">H", len(mpf_bytes) + 2) + bytes(mpf_bytes)

    # -- Assemble --
    out = io.BytesIO()
    out.write(soi)
    out.write(xmp_app1)
    out.write(mpf_app2)
    out.write(rest_of_primary)
    out.write(gainmap_jpeg)
    return out.getvalue()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_ultra_hdr_jpeg(
    sdr_img: Image.Image,
    peak_nits: int,
    output_path: str,
    icc_profile: bytes | None = None,
) -> str:
    """
    Create an Ultra HDR JPEG (ISO 21496-1 / Android compatible).

    Primary image carries Container:Directory XMP; gain map carries
    hdrgm: metadata in its own XMP. Gain map is downsampled to 1/4
    resolution for smaller file size.
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
    gm_xmp = _build_gainmap_xmp(peak_nits)
    gm_jpeg = _inject_xmp_into_jpeg(gm_jpeg, gm_xmp)

    # Primary image XMP (needs gain map JPEG size for Container:Directory)
    primary_xmp = _build_primary_xmp(peak_nits, len(gm_jpeg))

    # Build MPF
    mpf_jpeg = _build_mpf_jpeg(sdr_jpeg, gm_jpeg, primary_xmp)

    with open(output_path, "wb") as f:
        f.write(mpf_jpeg)
    return output_path
