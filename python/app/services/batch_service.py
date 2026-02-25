"""Batch export service: handles batch generation with progress reporting."""

import asyncio
import uuid
from typing import Callable
from app.core.models import (
    BatchRequest, BatchResponse, BatchStatus,
    GenerateRequest, ExportFormat,
)
from app.services.export_service import export_single


# In-memory batch job registry
_batch_jobs: dict[str, BatchStatus] = {}
_batch_cancel: dict[str, bool] = {}

# Progress callback type: (batch_id, status) -> None
ProgressCallback = Callable[[str, BatchStatus], None] | None

# Global progress callback (set by WebSocket handler)
_progress_callback: ProgressCallback = None


def set_progress_callback(callback: ProgressCallback) -> None:
    global _progress_callback
    _progress_callback = callback


def get_batch_status(batch_id: str) -> BatchStatus | None:
    return _batch_jobs.get(batch_id)


def cancel_batch(batch_id: str) -> bool:
    if batch_id in _batch_cancel:
        _batch_cancel[batch_id] = True
        return True
    return False


async def run_batch(request: BatchRequest) -> BatchResponse:
    """Start a batch export job. Returns immediately with batch ID."""
    batch_id = str(uuid.uuid4())[:8]

    # Calculate total images
    apl_values = list(range(
        request.apl_range_start,
        request.apl_range_end + 1,
        request.apl_step,
    ))
    total = len(apl_values)

    status = BatchStatus(
        batch_id=batch_id,
        status="running",
        total=total,
        completed=0,
        failed=0,
        current_apl=None,
    )
    _batch_jobs[batch_id] = status
    _batch_cancel[batch_id] = False

    # Run batch in background
    asyncio.create_task(_execute_batch(batch_id, request, apl_values))

    return BatchResponse(batch_id=batch_id)


async def _execute_batch(
    batch_id: str,
    request: BatchRequest,
    apl_values: list[int],
) -> None:
    """Execute batch generation in background."""
    status = _batch_jobs[batch_id]

    for apl in apl_values:
        # Check for cancellation
        if _batch_cancel.get(batch_id, False):
            status.status = "cancelled"
            _notify_progress(batch_id, status)
            break

        status.current_apl = apl
        _notify_progress(batch_id, status)

        try:
            gen_request = GenerateRequest(
                width=request.width,
                height=request.height,
                apl_percent=apl,
                shape=request.shape,
                color_space=request.color_space,
                hdr_mode=request.hdr_mode,
                hdr_peak_nits=request.hdr_peak_nits,
                hdr_video_peak_nits=request.hdr_video_peak_nits,
                export_format=request.export_format,
                output_directory=request.output_directory,
            )
            # Run CPU-bound export in thread pool
            await asyncio.to_thread(export_single, gen_request)
            status.completed += 1
        except Exception as e:
            status.failed += 1
            print(f"Batch {batch_id}: APL {apl}% failed: {e}")

        _notify_progress(batch_id, status)

    if status.status == "running":
        status.status = "completed" if status.failed == 0 else "failed"
    status.current_apl = None
    _notify_progress(batch_id, status)

    # Cleanup cancel flag
    _batch_cancel.pop(batch_id, None)


def _notify_progress(batch_id: str, status: BatchStatus) -> None:
    """Send progress update via callback."""
    if _progress_callback:
        try:
            _progress_callback(batch_id, status)
        except Exception:
            pass
