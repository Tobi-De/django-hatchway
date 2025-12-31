import json

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from hatchway import api_view
from hatchway.models import AuthToken


@pytest.mark.django_db
class TestAuthenticatedViews:
    def test_auth_required_returns_401_when_not_authenticated(self):
        @api_view.get(auth=True)
        def protected_view(request) -> dict:
            return {"data": "secret"}

        factory = RequestFactory()
        response = protected_view(factory.get("/"))

        assert response.status_code == 401
        assert json.loads(response.content)["error"] == "authentication_required"

    def test_auth_required_succeeds_with_valid_token(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        @api_view.get(auth=True)
        def protected_view(request) -> dict:
            return {"user_id": request.user.id}

        factory = RequestFactory()
        response = protected_view(
            factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        )

        assert response.status_code == 200
        assert json.loads(response.content)["user_id"] == user.id

    def test_auth_required_succeeds_with_session(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")

        @api_view.get(auth=True)
        def protected_view(request) -> dict:
            return {"username": request.user.username}

        factory = RequestFactory()
        request = factory.get("/")
        request.user = user

        response = protected_view(request)

        assert response.status_code == 200
        assert json.loads(response.content)["username"] == "testuser"

    def test_permission_required_returns_401_when_not_authenticated(self):
        @api_view.get(permissions=["auth.special_permission"])
        def protected_view(request) -> dict:
            return {"data": "secret"}

        factory = RequestFactory()
        response = protected_view(factory.get("/"))

        assert response.status_code == 401
        assert json.loads(response.content)["error"] == "authentication_required"

    def test_permission_required_returns_403_when_missing_permission(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        @api_view.get(auth=True, permissions=["auth.special_permission"])
        def protected_view(request) -> dict:
            return {"data": "secret"}

        factory = RequestFactory()
        response = protected_view(
            factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        )

        assert response.status_code == 403
        assert json.loads(response.content)["error"] == "permission_denied"

    def test_permission_required_succeeds_when_granted(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        # Grant permission
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.create(
            codename="special_permission",
            name="Can do special things",
            content_type=content_type,
        )
        user.user_permissions.add(permission)

        @api_view.get(auth=True, permissions=["auth.special_permission"])
        def protected_view(request) -> dict:
            return {"data": "secret"}

        factory = RequestFactory()
        response = protected_view(
            factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        )

        assert response.status_code == 200
        assert json.loads(response.content)["data"] == "secret"

    def test_multiple_permissions_all_required(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        content_type = ContentType.objects.get_for_model(User)
        perm1 = Permission.objects.create(
            codename="permission1", name="Permission 1", content_type=content_type
        )
        perm2 = Permission.objects.create(
            codename="permission2", name="Permission 2", content_type=content_type
        )

        # Grant only one permission
        user.user_permissions.add(perm1)

        @api_view.get(auth=True, permissions=["auth.permission1", "auth.permission2"])
        def protected_view(request) -> dict:
            return {"data": "secret"}

        factory = RequestFactory()
        response = protected_view(
            factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        )

        # Should fail because user lacks permission2
        assert response.status_code == 403
        assert json.loads(response.content)["error"] == "permission_denied"

        # Now grant the second permission
        user.user_permissions.add(perm2)

        response = protected_view(
            factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        )

        # Should succeed now
        assert response.status_code == 200
        assert json.loads(response.content)["data"] == "secret"

    def test_public_view_works_without_auth(self):
        @api_view.get
        def public_view(request) -> dict:
            return {"message": "public data"}

        factory = RequestFactory()
        response = public_view(factory.get("/"))

        assert response.status_code == 200
        assert json.loads(response.content)["message"] == "public data"

    def test_custom_backend_list(self):
        user = User.objects.create_user("testuser", "test@example.com", "password")
        token = AuthToken.create_token(user)

        # Only allow token authentication
        @api_view.get(auth=["hatchway.auth.TokenAuthBackend"])
        def api_only_view(request) -> dict:
            return {"user_id": request.user.id}

        factory = RequestFactory()

        # Token should work
        response = api_only_view(
            factory.get("/", HTTP_AUTHORIZATION=f"Token {token.key}")
        )
        assert response.status_code == 200

        # Session should not work (backend not in list)
        request = factory.get("/")
        request.user = user
        response = api_only_view(request)
        assert response.status_code == 401
