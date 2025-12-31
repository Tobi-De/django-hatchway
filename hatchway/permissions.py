from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


def check_permissions(
    user: "AbstractBaseUser | None", permissions: Sequence[str]
) -> tuple[bool, str | None]:
    """
    Check if user has all required permissions.

    Args:
        user: The user to check (may be None/AnonymousUser)
        permissions: List of permission strings like 'app.permission_name'

    Returns:
        (True, None) if user has all permissions
        (False, error_message) if user lacks any permission
    """
    if not user or not user.is_authenticated:
        return False, "authentication_required"

    for permission in permissions:
        if not user.has_perm(permission):
            return False, "permission_denied"

    return True, None


def require_authentication(
    user: "AbstractBaseUser | None",
) -> tuple[bool, str | None]:
    """
    Check if user is authenticated.

    Returns:
        (True, None) if authenticated
        (False, error_message) if not authenticated
    """
    if not user or not user.is_authenticated:
        return False, "authentication_required"
    return True, None
