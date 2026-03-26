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


def get_max_claws_per_user(session: Session) -> int:
    """
    Get the maximum number of claws per user from system settings

    Args:
        session: Database session

    Returns:
        Maximum claws per user (defaults to 10 if not set)
    """
    setting = get_system_setting(session, 'max_claws_per_user')
    if setting:
        try:
            return int(setting.value)
        except ValueError:
            return 10  # Fallback if value is invalid
    return 10  # Default if not found


def get_claw_apikey_daily_token_limit(session: Session) -> Optional[int]:
    """
    Get the daily token limit for claw auto-created API keys

    Args:
        session: Database session

    Returns:
        Daily token limit for claw API keys, or None if not set (should use default)
    """
    setting = get_system_setting(session, 'claw_apikey_daily_token_limit')
    if setting:
        try:
            value = int(setting.value)
            return value if value > 0 else None  # 0 means use default
        except ValueError:
            return None
    return None  # Default if not found


def get_system_settings_config(session: Session) -> dict:
    """
    Get all system settings config as a dictionary

    Args:
        session: Database session

    Returns:
        Dictionary with default_daily_token_limit, max_claws_per_user, claw_apikey_daily_token_limit
    """
    return {
        "default_daily_token_limit": get_default_daily_token_limit(session),
        "max_claws_per_user": get_max_claws_per_user(session),
        "claw_apikey_daily_token_limit": get_claw_apikey_daily_token_limit(session)
    }


def update_system_settings_config(
    session: Session,
    default_daily_token_limit: int,
    max_claws_per_user: int,
    claw_apikey_daily_token_limit: Optional[int] = None
) -> None:
    """
    Update multiple system settings config

    Args:
        session: Database session
        default_daily_token_limit: Default daily token limit for API keys
        max_claws_per_user: Maximum number of claws per user
        claw_apikey_daily_token_limit: Daily token limit for claw API keys (null for default)
    """
    set_system_setting(
        session,
        'default_daily_token_limit',
        str(default_daily_token_limit),
        'Default daily token limit for new API keys'
    )
    set_system_setting(
        session,
        'max_claws_per_user',
        str(max_claws_per_user),
        'Maximum number of claws each user can create'
    )
    if claw_apikey_daily_token_limit is not None:
        set_system_setting(
            session,
            'claw_apikey_daily_token_limit',
            str(claw_apikey_daily_token_limit),
            'Daily token limit for auto-created claw API keys (0 uses default)'
        )
