"""Batch job manager - encapsulates batch job state and operations."""

import asyncio
import time
import uuid
from typing import Callable
from app.core.config import CONFIG
from app.core.logging import get_logger
from app.core.models import (
    BatchRequest,
    BatchResponse,
    BatchStatus,
    GenerateRequest,
)
from app.services.export_service import export_single

_logger = get_logger(__name__)

# Progress callback type: (batch_id, status) -> None
ProgressCallback = Callable[[str, BatchStatus], None] | None


class BatchJobManager:
    """
    Manages batch job lifecycle with in-memory storage.
    Thread-safe singleton for managing batch export jobs.
    """

    def __init__(
        self,
        max_jobs: int = CONFIG.BATCH_MAX_JOBS,
        max_age_seconds: int = CONFIG.BATCH_MAX_AGE_SECONDS,
    ):
        self._jobs: dict[str, BatchStatus] = {}
        self._cancel_flags: dict[str, bool] = {}
        self._created_times: dict[str, float] = {}
        self._progress_callback: ProgressCallback = None
        self._max_jobs = max_jobs
        self._max_age_seconds = max_age_seconds

    _instance: "BatchJobManager | None" = None

    @classmethod
    def get_instance(cls) -> "BatchJobManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_status(self, batch_id: str) -> BatchStatus | None:
        """Get the status of a batch job."""
        return self._jobs.get(batch_id)

    def cancel(self, batch_id: str) -> bool:
        """Request cancellation of a batch job."""
        if batch_id in self._cancel_flags:
            self._cancel_flags[batch_id] = True
            return True
        return False

    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """Set the progress callback for WebSocket notifications."""
        self._progress_callback = callback

    def _prune_jobs(self) -> None:
        """Prune old/completed jobs to avoid unbounded memory growth."""
        now = time.time()

        # Remove old finished jobs.
        for batch_id, created in list(self._created_times.items()):
            status = self._jobs.get(batch_id)
            if not status:
                self._created_times.pop(batch_id, None)
                self._cancel_flags.pop(batch_id, None)
                continue
            if status.status != "running" and now - created > self._max_age_seconds:
                self._jobs.pop(batch_id, None)
                self._cancel_flags.pop(batch_id, None)
                self._created_times.pop(batch_id, None)

        # Cap total number of jobs, preferring to keep running ones.
        if len(self._jobs) <= self._max_jobs:
            return
        for batch_id in list(self._jobs.keys()):
            status = self._jobs.get(batch_id)
            if status and status.status != "running":
                self._jobs.pop(batch_id, None)
                self._cancel_flags.pop(batch_id, None)
                self._created_times.pop(batch_id, None)
                if len(self._jobs) <= self._max_jobs:
                    break

    def _notify_progress(self, batch_id: str, status: BatchStatus) -> None:
        """Send progress update via callback."""
        if self._progress_callback:
            try:
                self._progress_callback(batch_id, status)
            except Exception:
                pass

    async def create(self, request: BatchRequest) -> BatchResponse:
        """
        Start a batch export job.
        Returns immediately with batch ID.
        """
        batch_id = str(uuid.uuid4())[:8]

        # Calculate total images
        apl_values = list(
            range(
                request.apl_range_start,
                request.apl_range_end + 1,
                request.apl_step,
            )
        )
        total = len(apl_values)

        status = BatchStatus(
            batch_id=batch_id,
            status="running",
            total=total,
            completed=0,
            failed=0,
            current_apl=None,
        )
        self._jobs[batch_id] = status
        self._cancel_flags[batch_id] = False
        self._created_times[batch_id] = time.time()
        self._prune_jobs()

        # Run batch in background
        asyncio.create_task(self._execute_batch(batch_id, request, apl_values))

        return BatchResponse(batch_id=batch_id)

    async def _execute_batch(
        self,
        batch_id: str,
        request: BatchRequest,
        apl_values: list[int],
    ) -> None:
        """Execute batch generation in background."""
        status = self._jobs[batch_id]

        for apl in apl_values:
            # Check for cancellation
            if self._cancel_flags.get(batch_id, False):
                status.status = "cancelled"
                self._notify_progress(batch_id, status)
                break

            status.current_apl = apl
            self._notify_progress(batch_id, status)

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
                _logger.error(f"Batch {batch_id}: APL {apl}% failed: {e}")

            self._notify_progress(batch_id, status)

        if status.status == "running":
            status.status = "completed" if status.failed == 0 else "failed"
        status.current_apl = None
        self._notify_progress(batch_id, status)

        # Cleanup cancel flag
        self._cancel_flags.pop(batch_id, None)
        self._prune_jobs()


# Module-level functions for backward compatibility
_manager: BatchJobManager | None = None


def _get_manager() -> BatchJobManager:
    global _manager
    if _manager is None:
        _manager = BatchJobManager.get_instance()
    return _manager


def set_progress_callback(callback: ProgressCallback) -> None:
    """Set the progress callback for WebSocket notifications."""
    _get_manager().set_progress_callback(callback)


def get_batch_status(batch_id: str) -> BatchStatus | None:
    """Get the status of a batch job."""
    return _get_manager().get_status(batch_id)


def cancel_batch(batch_id: str) -> bool:
    """Request cancellation of a batch job."""
    return _get_manager().cancel(batch_id)


async def run_batch(request: BatchRequest) -> BatchResponse:
    """Start a batch export job. Returns immediately with batch ID."""
    return await _get_manager().create(request)
