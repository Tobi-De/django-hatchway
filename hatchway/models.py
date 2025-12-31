import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuthToken(models.Model):
    """
    Token for API authentication with expiration.
    """

    key = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_tokens",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token for {self.user} - {self.description or 'No description'}"

    @classmethod
    def create_token(cls, user, days_valid=4, description=""):
        """Create a new token for a user"""
        key = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(days=days_valid)
        return cls.objects.create(
            key=key, user=user, expires_at=expires_at, description=description
        )

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
