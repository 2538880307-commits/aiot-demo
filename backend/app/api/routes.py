from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas.health import HealthResponse
from app.services.ws_manager import ws_manager

router = APIRouter()


@router.get('/health', response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status='ok', service='backend')


@router.get('/api/v1/stats')
async def stats() -> dict:
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_detections': 0,
        'active_alerts': 0,
        'sites_online': 1,
    }


@router.websocket('/ws/alerts')
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({'type': 'pong'})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
