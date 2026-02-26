"""
Security helpers for the local FastAPI backend.

This backend is intended to be consumed only by the Electron app. To reduce
drive-by requests from arbitrary websites to 127.0.0.1, we support an optional
per-launch auth token enforced via:
  - HTTP header: X-C0lor-Mem-Token
  - WebSocket query param: ?token=...
"""

from __future__ import annotations

import os
from fastapi import Header, HTTPException, WebSocket

TOKEN_ENV = "C0LOR_MEM_AUTH_TOKEN"
ALLOWED_ORIGINS_ENV = "C0LOR_MEM_ALLOWED_ORIGINS"
TOKEN_HEADER = "X-C0lor-Mem-Token"


def get_expected_token() -> str | None:
    token = os.environ.get(TOKEN_ENV, "").strip()
    return token or None


def get_allowed_origins() -> list[str]:
    raw = os.environ.get(ALLOWED_ORIGINS_ENV, "null")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    # Electron file:// origin typically shows up as Origin: null.
    if "null" not in origins:
        origins.append("null")
    return origins


def require_token_header(
    x_c0lor_mem_token: str | None = Header(default=None, alias=TOKEN_HEADER),
) -> None:
    expected = get_expected_token()
    if not expected:
        return
    if x_c0lor_mem_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


async def enforce_ws_token(websocket: WebSocket) -> bool:
    expected = get_expected_token()
    if not expected:
        return True
    if websocket.query_params.get("token") != expected:
        # 1008 = Policy Violation
        await websocket.close(code=1008)
        return False
    return True
