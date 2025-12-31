"""
API endpoint performance benchmarks.

These benchmarks measure the performance of API views under various conditions.
Run with: pytest benchmarks/ --benchmark-only
"""

import json

import pytest
from django.test import RequestFactory

from .factories import CommentFactory, PostFactory, UserFactory, create_posts


@pytest.fixture
def request_factory():
    """Request factory for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def sample_user(db):
    """Create a sample user."""
    return UserFactory()


@pytest.fixture
def sample_posts(db):
    """Create sample posts for testing."""
    return create_posts(count=50, with_comments=True)


class TestListEndpointPerformance:
    """Benchmark list endpoint performance."""

    @pytest.mark.django_db
    def test_post_list_empty(self, benchmark, request_factory):
        """Benchmark post list with empty database."""
        from api.views import post_list

        request = request_factory.get("/api/posts/")

        result = benchmark(post_list, request)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_post_list_small(self, benchmark, request_factory):
        """Benchmark post list with 10 posts."""
        create_posts(count=10, with_comments=False)
        from api.views import post_list

        request = request_factory.get("/api/posts/")

        result = benchmark(post_list, request)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_post_list_medium(self, benchmark, request_factory, sample_posts):
        """Benchmark post list with 50 posts."""
        from api.views import post_list

        request = request_factory.get("/api/posts/")

        result = benchmark(post_list, request)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_post_list_large(self, benchmark, request_factory):
        """Benchmark post list with 200 posts."""
        create_posts(count=200, with_comments=True)
        from api.views import post_list

        request = request_factory.get("/api/posts/")

        result = benchmark(post_list, request)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_post_list_with_filters(self, benchmark, request_factory, sample_posts):
        """Benchmark post list with query filters."""
        from api.views import post_list

        # Note: tags parameter expects a list, so use multiple values
        request = request_factory.get("/api/posts/?published=true&limit=20&offset=10")

        result = benchmark(post_list, request)
        assert result.status_code == 200


class TestDetailEndpointPerformance:
    """Benchmark detail endpoint performance."""

    @pytest.mark.django_db
    def test_post_detail(self, benchmark, request_factory):
        """Benchmark single post retrieval."""
        post = PostFactory()
        # Add some comments to make it more realistic
        CommentFactory.create_batch(5, post=post)

        from api.views import post_detail

        request = request_factory.get(f"/api/posts/{post.id}/")

        result = benchmark(post_detail, request, id=post.id)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_post_detail_with_many_comments(self, benchmark, request_factory):
        """Benchmark post retrieval with many comments."""
        post = PostFactory()
        CommentFactory.create_batch(100, post=post)

        from api.views import post_detail

        request = request_factory.get(f"/api/posts/{post.id}/")

        result = benchmark(post_detail, request, id=post.id)
        assert result.status_code == 200


class TestCreateEndpointPerformance:
    """Benchmark create endpoint performance."""

    @pytest.mark.django_db
    def test_post_create_simple(self, benchmark, request_factory, sample_user):
        """Benchmark simple post creation."""
        from api.views import post_create

        data = {
            "title": "Test Post",
            "content": "This is test content",
            "author_id": sample_user.id,
            "published": False,
            "tags": ["test", "benchmark"],
        }

        request = request_factory.post(
            "/api/posts/create/",
            data=json.dumps(data),
            content_type="application/json",
        )

        result = benchmark(post_create, request)
        assert result.status_code == 201

    @pytest.mark.django_db
    def test_post_create_large_content(self, benchmark, request_factory, sample_user):
        """Benchmark post creation with large content."""
        from api.views import post_create

        # Generate large content (~10KB)
        large_content = " ".join(["word"] * 2000)

        data = {
            "title": "Test Post with Large Content",
            "content": large_content,
            "author_id": sample_user.id,
            "published": False,
            "tags": ["test"] * 20,
        }

        request = request_factory.post(
            "/api/posts/create/",
            data=json.dumps(data),
            content_type="application/json",
        )

        result = benchmark(post_create, request)
        assert result.status_code == 201


class TestUpdateEndpointPerformance:
    """Benchmark update endpoint performance."""

    @pytest.mark.django_db
    def test_post_update(self, benchmark, request_factory):
        """Benchmark post update."""
        post = PostFactory()

        from api.views import post_update

        data = {
            "title": "Updated Title",
            "published": True,
        }

        request = request_factory.patch(
            f"/api/posts/{post.id}/",
            data=json.dumps(data),
            content_type="application/json",
        )

        result = benchmark(post_update, request, id=post.id)
        assert result.status_code == 200


class TestSearchEndpointPerformance:
    """Benchmark search endpoint performance."""

    @pytest.mark.django_db
    def test_post_search_small(self, benchmark, request_factory):
        """Benchmark search with small dataset."""
        create_posts(count=20, with_comments=False)

        from api.views import post_search

        request = request_factory.get("/api/posts/search/?q=test")

        result = benchmark(post_search, request, q="test")
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_post_search_large(self, benchmark, request_factory):
        """Benchmark search with large dataset."""
        create_posts(count=200, with_comments=False)

        from api.views import post_search

        request = request_factory.get("/api/posts/search/?q=test")

        result = benchmark(post_search, request, q="test")
        assert result.status_code == 200


class TestBulkOperationsPerformance:
    """Benchmark bulk operations."""

    @pytest.mark.django_db
    def test_bulk_create_10(self, benchmark, request_factory, sample_user):
        """Benchmark bulk creation of 10 posts."""
        from api.views import post_bulk_create

        posts_data = [
            {
                "title": f"Bulk Post {i}",
                "content": f"Content for post {i}",
                "author_id": sample_user.id,
                "published": False,
                "tags": ["bulk"],
            }
            for i in range(10)
        ]

        data = {"posts": posts_data}

        request = request_factory.post(
            "/api/posts/bulk/",
            data=json.dumps(data),
            content_type="application/json",
        )

        result = benchmark(post_bulk_create, request)
        assert result.status_code == 201

    @pytest.mark.django_db
    def test_bulk_create_50(self, benchmark, request_factory, sample_user):
        """Benchmark bulk creation of 50 posts."""
        from api.views import post_bulk_create

        posts_data = [
            {
                "title": f"Bulk Post {i}",
                "content": f"Content for post {i}",
                "author_id": sample_user.id,
                "published": False,
                "tags": ["bulk"],
            }
            for i in range(50)
        ]

        data = {"posts": posts_data}

        request = request_factory.post(
            "/api/posts/bulk/",
            data=json.dumps(data),
            content_type="application/json",
        )

        result = benchmark(post_bulk_create, request)
        assert result.status_code == 201


class TestNestedResourcePerformance:
    """Benchmark nested resource operations."""

    @pytest.mark.django_db
    def test_post_comments_list(self, benchmark, request_factory):
        """Benchmark listing comments for a post."""
        post = PostFactory()
        CommentFactory.create_batch(20, post=post)

        from api.views import post_comments

        request = request_factory.get(f"/api/posts/{post.id}/comments/")

        result = benchmark(post_comments, request, post_id=post.id)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_comment_create(self, benchmark, request_factory):
        """Benchmark comment creation."""
        post = PostFactory()

        from api.views import post_comment_create

        data = {
            "author_name": "Test Author",
            "content": "Test comment content",
            "rating": 5,
        }

        request = request_factory.post(
            f"/api/posts/{post.id}/comments/create/",
            data=json.dumps(data),
            content_type="application/json",
        )

        result = benchmark(post_comment_create, request, post_id=post.id)
        assert result.status_code == 201
