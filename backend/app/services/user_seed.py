from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


DEFAULT_USERS = [
    {
        'username': 'admin',
        'employee_no': 'A0001',
        'name': '系统管理员',
        'department': '信息中心',
        'position': '系统管理员',
        'role': 'admin',
        'permissions': ['工具管理', '权限管理', '系统设置']
    },
    {
        'username': 'operator',
        'employee_no': 'E0001',
        'name': '现场值班员',
        'department': '车辆检修部',
        'position': '检修员',
        'role': 'employee',
        'permissions': ['工具管理']
    }
]


async def seed_users_if_empty(session: AsyncSession) -> None:
    total = await session.scalar(select(func.count()).select_from(User))
    if total and total > 0:
        return

    session.add_all([User(**item) for item in DEFAULT_USERS])
    await session.commit()
