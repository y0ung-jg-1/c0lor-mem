from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class Shape(str, Enum):
    RECTANGLE = "rectangle"
    CIRCLE = "circle"


class ColorSpace(str, Enum):
    REC709 = "rec709"
    DISPLAY_P3 = "displayP3"
    REC2020 = "rec2020"


class HdrMode(str, Enum):
    NONE = "none"
    APPLE_GAINMAP = "apple-gainmap"
    ULTRA_HDR = "ultra-hdr"


class ExportFormat(str, Enum):
    PNG = "png"
    JPEG = "jpeg"
    HEIF = "heif"
    H264 = "h264"
    H265 = "h265"


class GenerateRequest(BaseModel):
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
    apl_percent: int = Field(ge=1, le=100)
    shape: Shape = Shape.RECTANGLE
    color_space: ColorSpace = ColorSpace.REC709
    hdr_mode: HdrMode = HdrMode.NONE
    hdr_peak_nits: int = Field(default=1000, ge=200, le=10000)
    export_format: ExportFormat = ExportFormat.PNG
    output_directory: str = ""


class PreviewRequest(BaseModel):
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
    apl_percent: int = Field(ge=1, le=100)
    shape: Shape = Shape.RECTANGLE


class GenerateResponse(BaseModel):
    output_path: str
    file_size: int


class BatchRequest(BaseModel):
    width: int = Field(gt=0, le=8192)
    height: int = Field(gt=0, le=8192)
    apl_range_start: int = Field(ge=1, le=100)
    apl_range_end: int = Field(ge=1, le=100)
    apl_step: int = Field(default=1, ge=1, le=99)
    shape: Shape = Shape.RECTANGLE
    color_space: ColorSpace = ColorSpace.REC709
    hdr_mode: HdrMode = HdrMode.NONE
    hdr_peak_nits: int = Field(default=1000, ge=200, le=10000)
    export_format: ExportFormat = ExportFormat.PNG
    output_directory: str = ""


class BatchResponse(BaseModel):
    batch_id: str


class BatchStatus(BaseModel):
    batch_id: str
    status: Literal["running", "completed", "failed", "cancelled"]
    total: int
    completed: int
    failed: int
    current_apl: int | None = None
