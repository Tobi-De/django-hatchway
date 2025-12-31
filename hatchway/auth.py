from typing import TYPE_CHECKING, Protocol

from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser


class AuthBackend(Protocol):
    """Protocol for authentication backends"""

    def authenticate(self, request: HttpRequest) -> "AbstractBaseUser | None":
        """
        Attempt to authenticate the request.
        Returns User object if successful, None otherwise.
        """
        ...


class SessionAuthBackend:
    """Django session-based authentication"""

    def authenticate(self, request: HttpRequest) -> "AbstractBaseUser | None":
        if hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None


class TokenAuthBackend:
    """Token-based authentication (Authorization: Token <token>)"""

    def authenticate(self, request: HttpRequest) -> "AbstractBaseUser | None":
        # Lazy import to avoid circular dependency during Django startup
        from .models import AuthToken

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Token "):
            return None

        token = auth_header[6:]  # Remove 'Token ' prefix
        try:
            token_obj = AuthToken.objects.select_related("user").get(
                key=token, expires_at__gt=timezone.now()
            )
            return token_obj.user
        except AuthToken.DoesNotExist:
            return None


def get_backends(backend_paths: list[str] | None = None) -> list[AuthBackend]:
    """
    Get authentication backends from paths or Django settings.

    Args:
        backend_paths: List of backend class paths (e.g., ["hatchway.auth.TokenAuthBackend"])
                      If None, reads from HATCHWAY_AUTH_BACKENDS setting with default fallback

    Returns:
        List of instantiated backend objects
    """
    backend_paths = backend_paths or getattr(
        settings,
        "HATCHWAY_AUTH_BACKENDS",
        [
            "hatchway.auth.SessionAuthBackend",
            "hatchway.auth.TokenAuthBackend",
        ],
    )

    backends = []
    for path in backend_paths:
        module_path, class_name = path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        backend_class = getattr(module, class_name)
        backends.append(backend_class())

    return backends


def authenticate_request(
    request: HttpRequest, backends: list[AuthBackend] | None = None
) -> tuple["AbstractBaseUser | None", str | None]:
    """
    Try authentication backends in sequence.

    Returns:
        (user, backend_name) if successful
        (None, None) if all backends fail
    """
    if backends is None:
        backends = get_backends()

    for backend in backends:
        user = backend.authenticate(request)
        if user is not None:
            return user, backend.__class__.__name__

    return None, None
