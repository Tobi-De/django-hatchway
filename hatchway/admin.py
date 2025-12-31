from django.contrib import admin

from .models import AuthToken


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "description", "created_at", "expires_at", "is_expired"]
    list_filter = ["created_at", "expires_at"]
    search_fields = ["user__username", "user__email", "description"]
    readonly_fields = ["key", "created_at"]

    def is_expired(self, obj):
        return obj.is_expired

    is_expired.boolean = True
