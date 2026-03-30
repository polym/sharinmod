"""
Operation log decorator for tracking admin operations
"""
import asyncio
import functools
import logging
from typing import Optional, Callable, Any, ParamSpec
from inspect import signature, Parameter

from sqlmodel import Session

from api.models.operation_log import OperationType, ResourceType
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
            # Get current_user from kwargs (injected by Depends)
            current_user = kwargs.get('current_user')

            # Execute the function
            result = await func(*args, **kwargs)

            # Log the operation
            _log_operation_internal(
                current_user, operation_type, resource_type,
                resource_id_param, use_return_value, result, kwargs
            )

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            # Get current_user from kwargs (injected by Depends)
            current_user = kwargs.get('current_user')

            # Execute the function
            result = func(*args, **kwargs)

            # Log the operation
            _log_operation_internal(
                current_user, operation_type, resource_type,
                resource_id_param, use_return_value, result, kwargs
            )

            return result

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _log_operation_internal(
    current_user: Any,
    operation_type: OperationType,
    resource_type: ResourceType,
    resource_id_param: Optional[str],
    use_return_value: bool,
    return_value: Any,
    func_kwargs: dict
) -> None:
    """
    Internal function to log operation after execution.

    Args:
        current_user: Current authenticated user
        operation_type: Type of operation
        resource_type: Type of resource
        resource_id_param: Name of parameter containing resource_id
        use_return_value: Whether to extract resource_id from return value
        return_value: Return value from the function
        func_kwargs: Keyword arguments passed to the function
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

        # Get resource_id
        resource_id = None
        if use_return_value:
            # Extract from return value
            if hasattr(return_value, 'id'):
                resource_id = return_value.id
            elif isinstance(return_value, dict):
                resource_id = return_value.get('id')
            elif isinstance(return_value, int):
                resource_id = return_value
        elif resource_id_param:
            # Extract from function parameters
            resource_id = func_kwargs.get(resource_id_param)

        if resource_id is None:
            logger.warning(f"Cannot log operation: resource_id not found (param={resource_id_param}, use_return={use_return_value})")
            return

        # Create the log entry using a separate session internally
        create_operation_log(
            user_id=user_id,
            operation_type=operation_type,
            resource_type=resource_type,
            resource_id=resource_id
        )

    except Exception as e:
        # Log failure should not affect main business
        logger.error(f"Failed to log operation: {e}")
