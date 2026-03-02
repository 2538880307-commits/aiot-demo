from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import String, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.tool import Tool
from app.schemas.health import HealthResponse
from app.schemas.tool import ToolCreate, ToolListResponse, ToolOut, ToolUpdate
from app.services.ws_manager import ws_manager

router = APIRouter()


@router.get('/health', response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status='ok', service='backend')


@router.get('/api/v1/stats')
async def stats(db: AsyncSession = Depends(get_db)) -> dict:
    tools_total = await db.scalar(select(func.count()).select_from(Tool))
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_detections': int(tools_total or 0),
        'active_alerts': 0,
        'sites_online': 1,
    }


@router.get('/api/v1/tools', response_model=ToolListResponse)
async def list_tools(
    tool_code: str = Query(default=''),
    tool_type: str = Query(default=''),
    tool_name: str = Query(default=''),
    stock: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ToolListResponse:
    query = select(Tool)

    if tool_code:
        query = query.where(Tool.tool_code.ilike(f'%{tool_code.strip()}%'))
    if tool_type:
        query = query.where(Tool.tool_type == tool_type)
    if tool_name:
        query = query.where(Tool.tool_name.ilike(f'%{tool_name.strip()}%'))
    if stock:
        query = query.where(func.cast(Tool.stock, String).ilike(f'%{stock.strip()}%'))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    offset = (page - 1) * page_size
    items = (await db.scalars(query.order_by(Tool.id.desc()).offset(offset).limit(page_size))).all()

    return ToolListResponse(total=int(total or 0), items=[ToolOut.model_validate(item) for item in items])


@router.post('/api/v1/tools', response_model=ToolOut)
async def create_tool(payload: ToolCreate, db: AsyncSession = Depends(get_db)) -> ToolOut:
    exists = await db.scalar(select(Tool).where(Tool.tool_code == payload.tool_code))
    if exists:
        raise HTTPException(status_code=409, detail='工具编码已存在')

    tool = Tool(**payload.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return ToolOut.model_validate(tool)


@router.put('/api/v1/tools/{tool_id}', response_model=ToolOut)
async def update_tool(tool_id: int, payload: ToolUpdate, db: AsyncSession = Depends(get_db)) -> ToolOut:
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail='工具不存在')

    duplicate = await db.scalar(select(Tool).where(Tool.tool_code == payload.tool_code, Tool.id != tool_id))
    if duplicate:
        raise HTTPException(status_code=409, detail='工具编码已存在')

    for key, value in payload.model_dump().items():
        setattr(tool, key, value)

    await db.commit()
    await db.refresh(tool)
    return ToolOut.model_validate(tool)


@router.delete('/api/v1/tools/{tool_id}')
async def delete_tool(tool_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail='工具不存在')

    await db.delete(tool)
    await db.commit()
    return {'success': True}


@router.post('/api/v1/tools/batch-delete')
async def batch_delete_tools(payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    ids = payload.get('ids', [])
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail='ids 不能为空')

    await db.execute(delete(Tool).where(Tool.id.in_(ids)))
    await db.commit()
    return {'success': True}


@router.websocket('/ws/alerts')
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({'type': 'pong'})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
