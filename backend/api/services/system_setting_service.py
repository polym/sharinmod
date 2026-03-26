"""
Service layer for system settings management
"""
from sqlmodel import Session, select
from typing import Optional

from api.models.system_setting import SystemSetting


def get_system_setting(session: Session, key: str) -> Optional[SystemSetting]:
    """
    Get a system setting by key

    Args:
        session: Database session
        key: Setting key

    Returns:
        SystemSetting object or None if not found
    """
    statement = select(SystemSetting).where(SystemSetting.key == key)
    return session.exec(statement).first()


def set_system_setting(session: Session, key: str, value: str, description: Optional[str] = None) -> SystemSetting:
    """
    Set or update a system setting

    Args:
        session: Database session
        key: Setting key
        value: Setting value
        description: Optional description

    Returns:
        Updated or created SystemSetting object
    """
    setting = get_system_setting(session, key)

    if setting:
        # Update existing setting
        setting.value = value
        if description is not None:
            setting.description = description
        session.add(setting)
        session.commit()
        session.refresh(setting)
        return setting
    else:
        # Create new setting
        new_setting = SystemSetting(
            key=key,
            value=value,
            description=description
        )
        session.add(new_setting)
        session.commit()
        session.refresh(new_setting)
        return new_setting


def get_default_daily_token_limit(session: Session) -> int:
    """
    Get the default daily token limit from system settings

    Args:
        session: Database session

    Returns:
        Default daily token limit (defaults to 100000 if not set)
    """
    setting = get_system_setting(session, 'default_daily_token_limit')
    if setting:
        try:
            return int(setting.value)
        except ValueError:
            return 100000  # Fallback if value is invalid
    return 100000  # Default if not found


def get_all_system_settings(session: Session) -> dict:
    """
    Get all system settings as a dictionary

    Args:
        session: Database session

    Returns:
        Dictionary of key-value pairs for all settings
    """
    statement = select(SystemSetting)
    settings = session.exec(statement).all()
    return {setting.key: setting for setting in settings}
