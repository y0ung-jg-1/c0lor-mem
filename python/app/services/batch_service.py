"""Batch export service: handles batch generation with progress reporting.

This module provides backward-compatible module-level functions
that delegate to BatchJobManager singleton.
"""

# Re-export from batch_manager for backward compatibility
from app.services.batch_manager import (
    BatchJobManager,
    ProgressCallback,
    cancel_batch,
    get_batch_status,
    run_batch,
    set_progress_callback,
)

__all__ = [
    "BatchJobManager",
    "ProgressCallback",
    "cancel_batch",
    "get_batch_status",
    "run_batch",
    "set_progress_callback",
]
