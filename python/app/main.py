from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.api.modules.test_pattern import router as test_pattern_router, _ws_clients
from app.security import enforce_ws_token, get_allowed_origins, require_token_header, TOKEN_HEADER

app = FastAPI(title="c0lor-mem Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", TOKEN_HEADER],
)

app.include_router(test_pattern_router, prefix="/api/v1/test-pattern")


@app.get("/api/v1/health", dependencies=[Depends(require_token_header)])
async def health():
    return {"status": "ok"}


@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for batch progress updates."""
    if not await enforce_ws_token(websocket):
        return
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Client can send "cancel:{batch_id}" to cancel a job
            if data.startswith("cancel:"):
                from app.services.batch_service import cancel_batch
                batch_id = data.split(":", 1)[1]
                cancel_batch(batch_id)
    except WebSocketDisconnect:
        _ws_clients.discard(websocket)
