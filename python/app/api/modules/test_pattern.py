"""Test pattern API endpoints."""

import io
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from app.core.models import (
    GenerateRequest, PreviewRequest, GenerateResponse,
    BatchRequest, BatchResponse, BatchStatus,
)
from app.core.pattern_generator import generate_pattern_rgba
from app.services.export_service import export_single
from app.services.batch_service import (
    run_batch, get_batch_status, cancel_batch, set_progress_callback,
)

router = APIRouter()

# Connected WebSocket clients
_ws_clients: set[WebSocket] = set()


def _broadcast_progress(batch_id: str, status: BatchStatus) -> None:
    """Broadcast batch progress to all connected WebSocket clients."""
    message = json.dumps({
        "type": "batch_progress",
        "batch_id": batch_id,
        "status": status.status,
        "total": status.total,
        "completed": status.completed,
        "failed": status.failed,
        "current_apl": status.current_apl,
    })
    disconnected = set()
    for ws in _ws_clients:
        try:
            import asyncio
            asyncio.get_event_loop().create_task(ws.send_text(message))
        except Exception:
            disconnected.add(ws)
    _ws_clients -= disconnected


# Register progress callback
set_progress_callback(_broadcast_progress)


@router.post("/preview")
async def preview(request: PreviewRequest):
    """Generate a quick preview PNG thumbnail."""
    max_dim = 400
    scale = min(max_dim / request.width, max_dim / request.height, 1.0)
    preview_w = max(1, round(request.width * scale))
    preview_h = max(1, round(request.height * scale))

    img = generate_pattern_rgba(
        width=preview_w,
        height=preview_h,
        apl_percent=request.apl_percent,
        shape=request.shape,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate a single test pattern image."""
    return export_single(request)


@router.post("/batch", response_model=BatchResponse, status_code=202)
async def batch_generate(request: BatchRequest):
    """Start a batch generation job. Returns 202 with batch ID."""
    return await run_batch(request)


@router.get("/batch/{batch_id}/status", response_model=BatchStatus)
async def batch_status(batch_id: str):
    """Get batch job status."""
    status = get_batch_status(batch_id)
    if not status:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Batch not found")
    return status


@router.post("/batch/{batch_id}/cancel")
async def batch_cancel(batch_id: str):
    """Cancel a running batch job."""
    success = cancel_batch(batch_id)
    return {"cancelled": success}
