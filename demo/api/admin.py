from django.contrib import admin

from .models import Comment, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "published", "created_at", "comment_count"]
    list_filter = ["published", "created_at"]
    search_fields = ["title", "content"]
    date_hierarchy = "created_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author_name", "post", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["author_name", "content"]
    date_hierarchy = "created_at"
