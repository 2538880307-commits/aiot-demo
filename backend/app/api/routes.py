from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import String, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.tool import Tool
from app.models.user import User
from app.schemas.health import HealthResponse
from app.schemas.tool import ToolCreate, ToolListResponse, ToolOut, ToolUpdate
from app.schemas.user import (
    PermissionOptionsResponse,
    UserCreate,
    UserListResponse,
    UserOut,
    UserPermissionsUpdate,
    UserUpdate,
)
from app.services.ws_manager import ws_manager

router = APIRouter()
PERMISSION_OPTIONS = ['工具管理', '权限管理', '系统设置']


async def require_admin(requester_username: str, db: AsyncSession) -> User:
    requester = await db.scalar(select(User).where(User.username == requester_username))
    if not requester:
        raise HTTPException(status_code=404, detail='请求用户不存在')
    if requester.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可执行该操作')
    return requester


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


@router.get('/api/v1/permissions/options', response_model=PermissionOptionsResponse)
async def list_permission_options() -> PermissionOptionsResponse:
    return PermissionOptionsResponse(items=PERMISSION_OPTIONS)


@router.get('/api/v1/users/me', response_model=UserOut)
async def get_me(username: str = Query(...), db: AsyncSession = Depends(get_db)) -> UserOut:
    user = await db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')
    return UserOut.model_validate(user)


@router.get('/api/v1/users', response_model=UserListResponse)
async def list_users(
    requester_username: str = Query(...),
    employee_no: str = Query(default=''),
    name: str = Query(default=''),
    department: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    await require_admin(requester_username, db)

    query = select(User)
    if employee_no:
        query = query.where(User.employee_no.ilike(f'%{employee_no.strip()}%'))
    if name:
        query = query.where(User.name.ilike(f'%{name.strip()}%'))
    if department:
        query = query.where(User.department.ilike(f'%{department.strip()}%'))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * page_size
    items = (await db.scalars(query.order_by(User.id.desc()).offset(offset).limit(page_size))).all()
    return UserListResponse(total=int(total or 0), items=[UserOut.model_validate(item) for item in items])


@router.post('/api/v1/users', response_model=UserOut)
async def create_user(
    payload: UserCreate,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    await require_admin(requester_username, db)

    by_username = await db.scalar(select(User).where(User.username == payload.username))
    if by_username:
        raise HTTPException(status_code=409, detail='用户名已存在')

    by_employee_no = await db.scalar(select(User).where(User.employee_no == payload.employee_no))
    if by_employee_no:
        raise HTTPException(status_code=409, detail='工号已存在')

    permissions = [perm for perm in payload.permissions if perm in PERMISSION_OPTIONS]
    user = User(**payload.model_dump(exclude={'permissions'}), permissions=permissions)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.put('/api/v1/users/{user_id}', response_model=UserOut)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    await require_admin(requester_username, db)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    duplicate_username = await db.scalar(
        select(User).where(User.username == payload.username, User.id != user_id)
    )
    if duplicate_username:
        raise HTTPException(status_code=409, detail='用户名已存在')

    duplicate_employee_no = await db.scalar(
        select(User).where(User.employee_no == payload.employee_no, User.id != user_id)
    )
    if duplicate_employee_no:
        raise HTTPException(status_code=409, detail='工号已存在')

    for key, value in payload.model_dump().items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.put('/api/v1/users/{user_id}/permissions', response_model=UserOut)
async def update_user_permissions(
    user_id: int,
    payload: UserPermissionsUpdate,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    await require_admin(requester_username, db)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    user.permissions = [perm for perm in payload.permissions if perm in PERMISSION_OPTIONS]
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)




@router.delete('/api/v1/users/{user_id}')
async def delete_user(
    user_id: int,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    requester = await require_admin(requester_username, db)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    if user.id == requester.id:
        raise HTTPException(status_code=400, detail='不能删除当前登录管理员账号')

    await db.delete(user)
    await db.commit()
    return {'success': True}

@router.get('/api/v1/users/me/permissions')
async def get_my_permissions(username: str = Query(...), db: AsyncSession = Depends(get_db)) -> dict:
    user = await db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=404, detail='用户不存在')

    return {'username': user.username, 'permissions': user.permissions}


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
