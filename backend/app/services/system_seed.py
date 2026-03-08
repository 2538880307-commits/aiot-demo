from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting
from app.models.tool_type import ToolType


DEFAULT_SETTINGS = {
    'password_policy': {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_number': True,
        'require_special': False,
        'session_timeout_minutes': 120,
        'max_login_retries': 5,
    },
    'alert_threshold': {
        'low_stock_threshold': 5,
        'detection_confidence_threshold': 0.8,
        'alert_dedup_seconds': 60,
    },
}

DEFAULT_TOOL_TYPES = [
    {'name': '电动工具', 'description': '电驱动类工具', 'sort_order': 10, 'enabled': True},
    {'name': '手动工具', 'description': '人工操作类工具', 'sort_order': 20, 'enabled': True},
    {'name': '测量工具', 'description': '测量检测类工具', 'sort_order': 30, 'enabled': True},
    {'name': '安全设备', 'description': '安全防护设备', 'sort_order': 40, 'enabled': True},
]


async def seed_system_configs(session: AsyncSession) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        row = await session.scalar(select(SystemSetting).where(SystemSetting.setting_key == key))
        if not row:
            session.add(SystemSetting(setting_key=key, setting_value=value, updated_by='system'))

    for item in DEFAULT_TOOL_TYPES:
        exists = await session.scalar(select(ToolType).where(ToolType.name == item['name']))
        if not exists:
            session.add(ToolType(**item))

    await session.commit()
