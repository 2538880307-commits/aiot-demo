from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy import String, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.models.operation_log import OperationLog
from app.models.system_setting import SystemSetting
from app.models.tool import Tool
from app.models.tool_type import ToolType
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
from app.services.password_service import hash_password, verify_password
from app.services.tool_count_service import tool_count_service
from app.services.ws_manager import ws_manager

router = APIRouter()
PERMISSION_OPTIONS = ['工具管理', '工具识别', '权限管理', '系统设置']
SETTING_PASSWORD_POLICY = 'password_policy'
SETTING_ALERT_THRESHOLD = 'alert_threshold'


async def require_admin(requester_username: str, db: AsyncSession) -> User:
    requester = await db.scalar(select(User).where(User.username == requester_username))
    if not requester:
        raise HTTPException(status_code=404, detail='请求用户不存在')
    if requester.role != 'admin':
        raise HTTPException(status_code=403, detail='仅管理员可执行该操作')
    return requester


async def append_log(
    db: AsyncSession,
    module: str,
    action: str,
    actor: str,
    target: str = '',
    detail: dict | None = None,
) -> None:
    try:
        db.add(
            OperationLog(
                module=module,
                action=action,
                actor=actor,
                target=target,
                detail_json=detail or {},
            )
        )
        await db.commit()
    except Exception:
        await db.rollback()


async def get_setting_value(db: AsyncSession, key: str, fallback: dict) -> dict:
    row = await db.scalar(select(SystemSetting).where(SystemSetting.setting_key == key))
    if not row:
        row = SystemSetting(setting_key=key, setting_value=fallback, updated_by='system')
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return row.setting_value


@router.get('/health', response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status='ok', service='backend')


@router.post('/api/v1/auth/login')
async def login(payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    username = str(payload.get('username', '')).strip()
    password = str(payload.get('password', ''))

    if not username or not password:
        raise HTTPException(status_code=400, detail='用户名和密码不能为空')

    user = await db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=401, detail='用户名或密码错误')

    if not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail='用户名或密码错误')

    return {
        'username': user.username,
        'employee_no': user.employee_no,
        'name': user.name,
        'department': user.department,
        'position': user.position,
        'role': user.role,
        'permissions': user.permissions or [],
        'role_key': user.role,
        'display_name': user.name,
        'login_at': datetime.now(timezone.utc).isoformat(),
    }


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


@router.get('/api/v1/settings/password-policy')
async def get_password_policy(db: AsyncSession = Depends(get_db)) -> dict:
    fallback = {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_number': True,
        'require_special': False,
        'session_timeout_minutes': 120,
        'max_login_retries': 5,
    }
    value = await get_setting_value(db, SETTING_PASSWORD_POLICY, fallback)
    return {'setting_key': SETTING_PASSWORD_POLICY, 'setting_value': value}


@router.put('/api/v1/settings/password-policy')
async def update_password_policy(
    payload: dict,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_admin(requester_username, db)
    row = await db.scalar(select(SystemSetting).where(SystemSetting.setting_key == SETTING_PASSWORD_POLICY))
    if not row:
        row = SystemSetting(setting_key=SETTING_PASSWORD_POLICY)
        db.add(row)

    row.setting_value = payload
    row.updated_by = requester_username
    await db.commit()

    await append_log(
        db,
        module='系统设置',
        action='更新密码策略',
        actor=requester_username,
        target=SETTING_PASSWORD_POLICY,
        detail=payload,
    )
    return {'success': True, 'setting_value': payload}


@router.get('/api/v1/settings/alert-threshold')
async def get_alert_threshold(db: AsyncSession = Depends(get_db)) -> dict:
    fallback = {
        'low_stock_threshold': 5,
        'detection_confidence_threshold': 0.8,
        'alert_dedup_seconds': 60,
    }
    value = await get_setting_value(db, SETTING_ALERT_THRESHOLD, fallback)
    return {'setting_key': SETTING_ALERT_THRESHOLD, 'setting_value': value}


@router.put('/api/v1/settings/alert-threshold')
async def update_alert_threshold(
    payload: dict,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_admin(requester_username, db)
    row = await db.scalar(select(SystemSetting).where(SystemSetting.setting_key == SETTING_ALERT_THRESHOLD))
    if not row:
        row = SystemSetting(setting_key=SETTING_ALERT_THRESHOLD)
        db.add(row)

    row.setting_value = payload
    row.updated_by = requester_username
    await db.commit()

    await append_log(
        db,
        module='系统设置',
        action='更新告警阈值',
        actor=requester_username,
        target=SETTING_ALERT_THRESHOLD,
        detail=payload,
    )
    return {'success': True, 'setting_value': payload}


@router.get('/api/v1/settings/tool-types')
async def list_tool_types(include_disabled: bool = Query(default=True), db: AsyncSession = Depends(get_db)) -> dict:
    query = select(ToolType)
    if not include_disabled:
        query = query.where(ToolType.enabled.is_(True))
    rows = (await db.scalars(query.order_by(ToolType.sort_order.asc(), ToolType.id.asc()))).all()
    return {
        'items': [
            {
                'id': row.id,
                'name': row.name,
                'description': row.description,
                'sort_order': row.sort_order,
                'enabled': row.enabled,
            }
            for row in rows
        ]
    }


@router.get('/api/v1/settings/tool-types/options')
async def list_tool_type_options(db: AsyncSession = Depends(get_db)) -> dict:
    rows = (
        await db.scalars(
            select(ToolType).where(ToolType.enabled.is_(True)).order_by(ToolType.sort_order.asc(), ToolType.id.asc())
        )
    ).all()
    return {'items': [row.name for row in rows]}


@router.post('/api/v1/settings/tool-types')
async def create_tool_type(
    payload: dict,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_admin(requester_username, db)

    name = str(payload.get('name', '')).strip()
    if not name:
        raise HTTPException(status_code=400, detail='类型名称不能为空')

    exists = await db.scalar(select(ToolType).where(ToolType.name == name))
    if exists:
        raise HTTPException(status_code=409, detail='工具类型已存在')

    row = ToolType(
        name=name,
        description=str(payload.get('description', '')).strip(),
        sort_order=int(payload.get('sort_order', 100)),
        enabled=bool(payload.get('enabled', True)),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    await append_log(
        db,
        module='系统设置',
        action='新增工具类型',
        actor=requester_username,
        target=row.name,
        detail={'tool_type_id': row.id},
    )
    return {
        'id': row.id,
        'name': row.name,
        'description': row.description,
        'sort_order': row.sort_order,
        'enabled': row.enabled,
    }


@router.put('/api/v1/settings/tool-types/{tool_type_id}')
async def update_tool_type(
    tool_type_id: int,
    payload: dict,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_admin(requester_username, db)

    row = await db.get(ToolType, tool_type_id)
    if not row:
        raise HTTPException(status_code=404, detail='工具类型不存在')

    name = str(payload.get('name', row.name)).strip()
    if not name:
        raise HTTPException(status_code=400, detail='类型名称不能为空')

    duplicate = await db.scalar(select(ToolType).where(ToolType.name == name, ToolType.id != tool_type_id))
    if duplicate:
        raise HTTPException(status_code=409, detail='工具类型已存在')

    old_name = row.name
    row.name = name
    row.description = str(payload.get('description', row.description)).strip()
    row.sort_order = int(payload.get('sort_order', row.sort_order))
    row.enabled = bool(payload.get('enabled', row.enabled))

    if old_name != row.name:
        tools = (await db.scalars(select(Tool).where(Tool.tool_type == old_name))).all()
        for item in tools:
            item.tool_type = row.name

    await db.commit()

    await append_log(
        db,
        module='系统设置',
        action='修改工具类型',
        actor=requester_username,
        target=row.name,
        detail={'tool_type_id': row.id},
    )
    return {
        'id': row.id,
        'name': row.name,
        'description': row.description,
        'sort_order': row.sort_order,
        'enabled': row.enabled,
    }


@router.delete('/api/v1/settings/tool-types/{tool_type_id}')
async def delete_tool_type(
    tool_type_id: int,
    requester_username: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_admin(requester_username, db)

    row = await db.get(ToolType, tool_type_id)
    if not row:
        raise HTTPException(status_code=404, detail='工具类型不存在')

    using_count = await db.scalar(select(func.count()).select_from(Tool).where(Tool.tool_type == row.name))
    if using_count and using_count > 0:
        raise HTTPException(status_code=409, detail='该工具类型仍在使用，无法删除')

    deleted_name = row.name
    await db.delete(row)
    await db.commit()

    await append_log(
        db,
        module='系统设置',
        action='删除工具类型',
        actor=requester_username,
        target=deleted_name,
        detail={'tool_type_id': tool_type_id},
    )
    return {'success': True}


@router.get('/api/v1/settings/operation-logs')
async def list_operation_logs(
    requester_username: str = Query(...),
    module: str = Query(default=''),
    action: str = Query(default=''),
    actor: str = Query(default=''),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_admin(requester_username, db)

    query = select(OperationLog)
    if module:
        query = query.where(OperationLog.module.ilike(f'%{module.strip()}%'))
    if action:
        query = query.where(OperationLog.action.ilike(f'%{action.strip()}%'))
    if actor:
        query = query.where(OperationLog.actor.ilike(f'%{actor.strip()}%'))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * page_size
    items = (await db.scalars(query.order_by(OperationLog.timestamp.desc()).offset(offset).limit(page_size))).all()

    return {
        'total': int(total or 0),
        'items': [
            {
                'id': row.id,
                'module': row.module,
                'action': row.action,
                'actor': row.actor,
                'target': row.target,
                'detail_json': row.detail_json,
                'timestamp': row.timestamp.isoformat() if row.timestamp else '',
            }
            for row in items
        ],
    }


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
    user = User(
        **payload.model_dump(exclude={'permissions', 'password'}),
        password_hash=hash_password(payload.password),
        permissions=permissions,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await append_log(
        db,
        module='权限管理',
        action='新增用户',
        actor=requester_username,
        target=user.username,
        detail={'user_id': user.id},
    )
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

    await append_log(
        db,
        module='权限管理',
        action='修改用户',
        actor=requester_username,
        target=user.username,
        detail={'user_id': user.id},
    )
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

    await append_log(
        db,
        module='权限管理',
        action='分配权限',
        actor=requester_username,
        target=user.username,
        detail={'permissions': user.permissions},
    )
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

    deleted_username = user.username
    await db.delete(user)
    await db.commit()

    await append_log(
        db,
        module='权限管理',
        action='删除用户',
        actor=requester_username,
        target=deleted_username,
        detail={'user_id': user_id},
    )
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

    valid_type = await db.scalar(select(ToolType).where(ToolType.name == payload.tool_type, ToolType.enabled.is_(True)))
    if not valid_type:
        raise HTTPException(status_code=400, detail='工具类型无效或已禁用')

    tool = Tool(**payload.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)

    await append_log(
        db,
        module='工具管理',
        action='新增工具',
        actor='system',
        target=tool.tool_code,
        detail={'tool_id': tool.id},
    )
    return ToolOut.model_validate(tool)


@router.put('/api/v1/tools/{tool_id}', response_model=ToolOut)
async def update_tool(tool_id: int, payload: ToolUpdate, db: AsyncSession = Depends(get_db)) -> ToolOut:
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail='工具不存在')

    duplicate = await db.scalar(select(Tool).where(Tool.tool_code == payload.tool_code, Tool.id != tool_id))
    if duplicate:
        raise HTTPException(status_code=409, detail='工具编码已存在')

    valid_type = await db.scalar(select(ToolType).where(ToolType.name == payload.tool_type, ToolType.enabled.is_(True)))
    if not valid_type:
        raise HTTPException(status_code=400, detail='工具类型无效或已禁用')

    for key, value in payload.model_dump().items():
        setattr(tool, key, value)

    await db.commit()
    await db.refresh(tool)

    await append_log(
        db,
        module='工具管理',
        action='修改工具',
        actor='system',
        target=tool.tool_code,
        detail={'tool_id': tool.id},
    )
    return ToolOut.model_validate(tool)


@router.delete('/api/v1/tools/{tool_id}')
async def delete_tool(tool_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail='工具不存在')

    code = tool.tool_code
    await db.delete(tool)
    await db.commit()

    await append_log(
        db,
        module='工具管理',
        action='删除工具',
        actor='system',
        target=code,
        detail={'tool_id': tool_id},
    )
    return {'success': True}


@router.post('/api/v1/tools/batch-delete')
async def batch_delete_tools(payload: dict, db: AsyncSession = Depends(get_db)) -> dict:
    ids = payload.get('ids', [])
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=400, detail='ids 不能为空')

    await db.execute(delete(Tool).where(Tool.id.in_(ids)))
    await db.commit()

    await append_log(
        db,
        module='工具管理',
        action='批量删除工具',
        actor='system',
        target='batch',
        detail={'ids': ids},
    )
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

@router.post('/api/v1/tool-count/detect')
async def detect_tool_count(
    image: UploadFile = File(...),
    requester_username: str = Query(default='system'),
    db: AsyncSession = Depends(get_db),
) -> dict:
    settings = get_settings()
    actor = requester_username.strip() or 'system'

    if not image.filename:
        await append_log(
            db,
            module='工具识别',
            action='识别失败',
            actor=actor,
            target='upload',
            detail={'reason': 'empty_filename'},
        )
        raise HTTPException(status_code=400, detail='图片文件不能为空')

    image_bytes = await image.read()
    max_size = settings.tool_count_max_image_mb * 1024 * 1024
    if len(image_bytes) > max_size:
        await append_log(
            db,
            module='工具识别',
            action='识别失败',
            actor=actor,
            target=image.filename,
            detail={'reason': 'image_too_large', 'size': len(image_bytes), 'max_size': max_size},
        )
        raise HTTPException(status_code=400, detail=f'图片大小不能超过 {settings.tool_count_max_image_mb}MB')

    try:
        result = tool_count_service.detect(image_bytes, image.filename)
        await append_log(
            db,
            module='工具识别',
            action='识别成功',
            actor=actor,
            target=image.filename,
            detail={
                'ready': bool(result.get('ready', False)),
                'total_count': int(result.get('total_count', 0) or 0),
                'by_class': result.get('by_class', {}),
            },
        )
        return result
    except RuntimeError as exc:
        result = {
            'ready': False,
            'message': str(exc),
            'total_count': 0,
            'by_class': {},
            'detections': [],
            'filename': image.filename,
        }
        await append_log(
            db,
            module='工具识别',
            action='识别失败',
            actor=actor,
            target=image.filename,
            detail={'reason': 'runtime_error', 'message': str(exc)},
        )
        return result
