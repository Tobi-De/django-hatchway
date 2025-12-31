from django.urls import path

from hatchway import methods

from . import views

urlpatterns = [
    # OpenAPI Documentation
    path("docs/", views.swagger_ui, name="swagger_ui"),
    path("openapi.yaml", views.openapi_schema, name="openapi_schema"),
    # Health check
    path("health/", views.health_check, name="health_check"),
    # Post list and creation
    path("posts/", views.post_list, name="post_list"),
    path("posts/create/", views.post_create, name="post_create"),
    path(
        "posts/create-with-file/",
        views.post_create_with_file,
        name="post_create_with_file",
    ),
    path("posts/bulk/", views.post_bulk_create, name="post_bulk_create"),
    # Post detail, update, delete - demonstrates methods() helper
    path(
        "posts/<int:id>/",
        methods(
            get=views.post_detail,
            patch=views.post_update,
            delete=views.post_delete,
        ),
        name="post_detail",
    ),
    # Post search and stats
    path("posts/search/", views.post_search, name="post_search"),
    path("posts/<int:id>/stats/", views.post_stats, name="post_stats"),
    # Post filtering
    path("posts/filter/", views.post_filter_advanced, name="post_filter_advanced"),
    # Post utilities
    path("posts/titles/", views.post_titles, name="post_titles"),
    path("posts/tags/summary/", views.post_tags_summary, name="post_tags_summary"),
    # Comments (nested under posts)
    path("posts/<int:post_id>/comments/", views.post_comments, name="post_comments"),
    path(
        "posts/<int:post_id>/comments/create/",
        views.post_comment_create,
        name="post_comment_create",
    ),
]
