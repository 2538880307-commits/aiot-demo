from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.password_service import hash_password


DEFAULT_USERS = [
    {
        'username': 'admin',
        'employee_no': 'A0001',
        'name': '系统管理员',
        'department': '信息中心',
        'position': '系统管理员',
        'role': 'admin',
        'password_hash': hash_password('Admin@123'),
        'permissions': ['工具管理', '权限管理', '系统设置']
    },
    {
        'username': 'operator',
        'employee_no': 'E0001',
        'name': '现场值班员',
        'department': '车辆检修部',
        'position': '检修员',
        'role': 'employee',
        'password_hash': hash_password('Operator@123'),
        'permissions': ['工具管理']
    }
]


async def seed_users_if_empty(session: AsyncSession) -> None:
    total = await session.scalar(select(func.count()).select_from(User))
    if total and total > 0:
        return

    session.add_all([User(**item) for item in DEFAULT_USERS])
    await session.commit()


async def patch_default_user_passwords(session: AsyncSession) -> None:
    fallback_map = {
        'admin': 'Admin@123',
        'operator': 'Operator@123',
    }
    rows = (await session.scalars(select(User).where(User.password_hash.is_(None)))).all()
    changed = False
    for row in rows:
        pwd = fallback_map.get(row.username)
        if not pwd:
            continue
        row.password_hash = hash_password(pwd)
        changed = True

    if changed:
        await session.commit()
