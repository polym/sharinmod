"""
Operation log decorator for tracking admin operations
"""
import asyncio
import functools
import logging
from typing import Optional, Callable, Any, ParamSpec
from inspect import signature, Parameter

from sqlmodel import Session, select

from api.models.operation_log import OperationType, ResourceType
from api.models.user import User
from api.models.unified_api_key import UnifiedAPIKey
from api.models.shared_api_key import SharedAPIKey
from api.models.claw import Claw
from api.models.provider_config import ProviderConfig, ProviderModel
from api.services.operation_log_service import create_operation_log

logger = logging.getLogger(__name__)

P = ParamSpec('P')


def log_operation(
    resource_type: ResourceType,
    operation_type: OperationType = OperationType.CREATE,
    resource_id_param: Optional[str] = None,
    use_return_value: bool = False
):
    """
    Decorator factory for logging operations.

    Args:
        resource_type: Type of resource being operated on
        operation_type: Type of operation (default: CREATE)
        resource_id_param: Name of parameter containing resource_id (e.g., "id", "user_id", "claw_id")
        use_return_value: If True, extract resource_id from return value instead of parameters

    Examples:
        # Extract resource_id from 'id' parameter
        @log_operation(USER, resource_id_param="id")
        def delete_user(id: int, db: Session):
            ...

        # Extract resource_id from 'user_id' parameter
        @log_operation(USER, DISABLE, resource_id_param="user_id")
        def disable_user(user_id: int, db: Session):
            ...

        # Extract resource_id from return value (e.g., created object)
        @log_operation(USER, use_return_value=True)
        def create_user(user_data: UserCreate, db: Session):
            ...  # returns created user object with id

        # For restart operations
        @log_operation(CLAW, RESTART, resource_id_param="id")
        def restart_claw(id: int, db: Session):
            ...
    """
    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # Get current_user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db') or kwargs.get('session')

            # For DELETE operations, get resource name before deleting
            resource_name_before_delete = None
            if operation_type == OperationType.DELETE and db and not use_return_value and resource_id_param:
                resource_id = kwargs.get(resource_id_param)
                if resource_id:
                    resource_name_before_delete = _get_resource_name(db, resource_type, resource_id)

            # Execute the function
            result = await func(*args, **kwargs)

            # Log the operation
            _log_operation_internal(
                current_user, db, operation_type, resource_type,
                resource_id_param, use_return_value, result, kwargs,
                resource_name_before_delete=resource_name_before_delete
            )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # Get current_user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db') or kwargs.get('session')

            # For DELETE operations, get resource name before deleting
            resource_name_before_delete = None
            if operation_type == OperationType.DELETE and db and not use_return_value and resource_id_param:
                resource_id = kwargs.get(resource_id_param)
                if resource_id:
                    resource_name_before_delete = _get_resource_name(db, resource_type, resource_id)

            # Execute the function
            result = func(*args, **kwargs)

            # Log the operation
            _log_operation_internal(
                current_user, db, operation_type, resource_type,
                resource_id_param, use_return_value, result, kwargs,
                resource_name_before_delete=resource_name_before_delete
            )

            return result

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _get_resource_name(db: Session, resource_type: ResourceType, resource_id: int) -> Optional[str]:
    """
    Query resource name from database for non-CREATE operations.

    Args:
        db: Database session
        resource_type: Type of resource
        resource_id: ID of resource

    Returns:
        Resource name or None
    """
    try:
        if resource_type == ResourceType.USER:
            user = db.exec(select(User).where(User.id == resource_id)).first()
            return user.name if user else None

        elif resource_type == ResourceType.CLAW:
            claw = db.exec(select(Claw).where(Claw.id == resource_id)).first()
            return claw.name if claw else None

        elif resource_type == ResourceType.PROVIDER:
            provider = db.exec(select(ProviderConfig).where(ProviderConfig.id == resource_id)).first()
            return provider.name if provider else None

        elif resource_type == ResourceType.PROVIDER_MODEL:
            model = db.exec(select(ProviderModel).where(ProviderModel.id == resource_id)).first()
            return model.display_name if model else None

        elif resource_type == ResourceType.UNIFIED_API_KEY:
            api_key = db.exec(select(UnifiedAPIKey).where(UnifiedAPIKey.id == resource_id)).first()
            return api_key.api_key_name if api_key else None

        elif resource_type == ResourceType.SHARED_API_KEY:
            shared_key = db.exec(select(SharedAPIKey).where(SharedAPIKey.id == resource_id)).first()
            if shared_key and shared_key.api_key_metadata:
                try:
                    import json
                    metadata = json.loads(shared_key.api_key_metadata)
                    return metadata.get('name')
                except Exception:
                    pass
            return None

        return None
    except Exception as e:
        logger.warning(f"Failed to get resource name: {e}")
        return None


def _log_operation_internal(
    current_user: Any,
    db: Optional[Session],
    operation_type: OperationType,
    resource_type: ResourceType,
    resource_id_param: Optional[str],
    use_return_value: bool,
    return_value: Any,
    func_kwargs: dict,
    resource_name_before_delete: Optional[str] = None
) -> None:
    """
    Internal function to log operation after execution.

    Args:
        current_user: Current authenticated user
        db: Database session
        operation_type: Type of operation
        resource_type: Type of resource
        resource_id_param: Name of parameter containing resource_id
        use_return_value: Whether to extract resource_id from return value
        return_value: Return value from the function
        func_kwargs: Keyword arguments passed to the function
        resource_name_before_delete: Resource name captured before deletion (for DELETE operations)
    """
    try:
        # Get user_id
        if current_user is None:
            logger.warning("Cannot log operation: current_user not found")
            return

        user_id = getattr(current_user, 'id', None)
        if user_id is None:
            logger.warning("Cannot log operation: current_user has no id")
            return

        # Get resource_id and resource_name
        resource_id = None
        resource_name = None
        if use_return_value:
            # Extract from return value (CREATE operation)
            if hasattr(return_value, 'id'):
                resource_id = return_value.id
                # Extract resource_name based on resource_type
                if resource_type == ResourceType.USER:
                    resource_name = getattr(return_value, 'name', None) or getattr(return_value, 'email', None)
                elif resource_type == ResourceType.CLAW:
                    resource_name = getattr(return_value, 'name', None)
                elif resource_type == ResourceType.PROVIDER:
                    resource_name = getattr(return_value, 'name', None)
                elif resource_type == ResourceType.PROVIDER_MODEL:
                    resource_name = getattr(return_value, 'display_name', None) or getattr(return_value, 'model_key', None)
                elif resource_type == ResourceType.UNIFIED_API_KEY:
                    resource_name = getattr(return_value, 'api_key_name', None)
                elif resource_type == ResourceType.SHARED_API_KEY:
                    # Try to get name from metadata
                    metadata = getattr(return_value, 'api_key_metadata', None)
                    if metadata:
                        try:
                            import json
                            parsed = json.loads(metadata)
                            resource_name = parsed.get('name')
                        except (json.JSONDecodeError, Exception):
                            pass
            elif isinstance(return_value, dict):
                resource_id = return_value.get('id')
                resource_name = return_value.get('name') or return_value.get('api_key_name') or return_value.get('display_name')
            elif isinstance(return_value, int):
                resource_id = return_value
        elif resource_id_param:
            # Extract from function parameters (non-CREATE operation)
            resource_id = func_kwargs.get(resource_id_param)
            # Use pre-captured name for DELETE operations
            if operation_type == OperationType.DELETE:
                resource_name = resource_name_before_delete
            # Query database to get resource name for other operations
            elif db and resource_id:
                resource_name = _get_resource_name(db, resource_type, resource_id)

        if resource_id is None:
            logger.warning(f"Cannot log operation: resource_id not found (param={resource_id_param}, use_return={use_return_value})")
            return

        # Create the log entry using a separate session internally
        create_operation_log(
            user_id=user_id,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name
        )

    except Exception as e:
        # Log failure should not affect main business
        logger.error(f"Failed to log operation: {e}")
