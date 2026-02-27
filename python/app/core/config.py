"""Application configuration constants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Immutable configuration class."""

    PORT_MIN: int = 18100
    PORT_MAX: int = 18200
    BATCH_MAX_JOBS: int = 50
    BATCH_MAX_AGE_SECONDS: int = 3600


CONFIG = Config()
