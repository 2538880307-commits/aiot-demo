from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import Tool


DEFAULT_TOOLS = [
    {'tool_code': '01001', 'tool_type': '电动工具', 'tool_name': '冲击电钻', 'stock': 6, 'team': '维修一组', 'image_url': ''},
    {'tool_code': '09010', 'tool_type': '手动工具', 'tool_name': '手动扳手', 'stock': 34, 'team': '维修一组', 'image_url': ''},
    {'tool_code': '07003', 'tool_type': '手动工具', 'tool_name': '套筒扳手', 'stock': 21, 'team': '维修一组', 'image_url': ''},
    {'tool_code': '09006', 'tool_type': '手动工具', 'tool_name': '手动螺丝刀', 'stock': 16, 'team': '维修二组', 'image_url': ''},
    {'tool_code': '07012', 'tool_type': '电动工具', 'tool_name': '电动角磨机', 'stock': 4, 'team': '维修二组', 'image_url': ''},
    {'tool_code': '09003', 'tool_type': '手动工具', 'tool_name': '手动钢丝钳', 'stock': 13, 'team': '维修一组', 'image_url': ''}
]


async def seed_tools_if_empty(session: AsyncSession) -> None:
    total = await session.scalar(select(func.count()).select_from(Tool))
    if total and total > 0:
        return

    session.add_all([Tool(**item) for item in DEFAULT_TOOLS])
    await session.commit()
