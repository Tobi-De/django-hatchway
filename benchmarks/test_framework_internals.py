"""
Framework internals performance benchmarks.

These benchmarks measure the performance of core Hatchway components:
- Parameter extraction and validation
- Schema serialization
- Type introspection
- Request processing overhead
"""

import msgspec
import pytest
from django.test import RequestFactory

from hatchway import Body, Query, QueryOrBody, Schema, api_view


class TestParameterExtractionPerformance:
    """Benchmark parameter extraction and validation."""

    def test_simple_query_params(self, benchmark):
        """Benchmark extraction of simple query parameters."""
        from hatchway.view import ApiView

        @api_view.get
        def test_view(request, a: int, b: str = "default", c: bool = False):
            return {"a": a, "b": b, "c": c}

        factory = RequestFactory()
        request = factory.get("/test/?a=42&b=hello&c=true")

        result = benchmark(test_view, request)
        assert result.status_code == 200

    def test_complex_query_params(self, benchmark):
        """Benchmark extraction of complex query parameters."""
        from hatchway.view import ApiView

        @api_view.get
        def test_view(
            request,
            ids: list[int] = [],
            tags: list[str] = [],
            published: bool | None = None,
            limit: int = 10,
            offset: int = 0,
        ):
            return {"count": len(ids)}

        factory = RequestFactory()
        request = factory.get(
            "/test/?ids=1&ids=2&ids=3&tags=a&tags=b&published=true&limit=20"
        )

        result = benchmark(test_view, request)
        assert result.status_code == 200

    def test_body_validation(self, benchmark):
        """Benchmark body parameter validation."""

        class TestSchema(Schema):
            title: str
            count: int
            tags: list[str]
            active: bool = True

        @api_view.post
        def test_view(request, data: TestSchema):
            return {"title": data.title}

        factory = RequestFactory()
        import json

        request = factory.post(
            "/test/",
            data=json.dumps(
                {
                    "title": "Test",
                    "count": 42,
                    "tags": ["a", "b", "c"],
                    "active": False,
                }
            ),
            content_type="application/json",
        )

        result = benchmark(test_view, request)
        assert result.status_code == 200

    def test_mixed_sources(self, benchmark):
        """Benchmark mixed parameter sources."""

        class BodyData(Schema):
            name: str
            value: int

        @api_view.post
        def test_view(
            request,
            id: int,
            mode: Query[str] = "default",
            data: BodyData = None,
            flag: QueryOrBody[bool] = False,
        ):
            return {"id": id}

        factory = RequestFactory()
        import json

        request = factory.post(
            "/test/?mode=test&flag=true",
            data=json.dumps({"name": "test", "value": 100}),
            content_type="application/json",
        )

        result = benchmark(test_view, request, id=42)
        assert result.status_code == 200


class TestSchemaSerializationPerformance:
    """Benchmark schema serialization."""

    @pytest.mark.django_db
    def test_simple_schema(self, benchmark):
        """Benchmark simple schema serialization."""
        from api.models import Post

        from .factories import PostFactory

        post = PostFactory()

        from api.schemas import PostListSchema

        def serialize():
            return PostListSchema.from_orm(post).dict()

        result = benchmark(serialize)
        assert "id" in result

    @pytest.mark.django_db
    def test_complex_schema(self, benchmark):
        """Benchmark complex schema serialization."""
        from api.models import Post

        from .factories import CommentFactory, PostFactory

        post = PostFactory()
        CommentFactory.create_batch(10, post=post)

        from api.schemas import PostSchema

        def serialize():
            return PostSchema.from_orm(post).dict()

        result = benchmark(serialize)
        assert "comment_count" in result

    @pytest.mark.django_db
    def test_list_serialization(self, benchmark):
        """Benchmark list serialization."""
        from .factories import create_posts

        posts = create_posts(count=50, with_comments=False)

        from api.schemas import PostListSchema

        def serialize():
            return [PostListSchema.from_orm(post).dict() for post in posts]

        result = benchmark(serialize)
        assert len(result) == 50


class TestTypeIntrospectionPerformance:
    """Benchmark type introspection and annotation parsing."""

    def test_sources_for_input(self, benchmark):
        """Benchmark sources_for_input method."""
        from hatchway.view import ApiView

        def get_sources():
            ApiView.sources_for_input(int)
            ApiView.sources_for_input(Query[str])
            ApiView.sources_for_input(Body[dict])
            ApiView.sources_for_input(list[int])

        benchmark(get_sources)

    def test_extract_signifier(self, benchmark):
        """Benchmark extract_signifier function."""
        from hatchway.types import Query, extract_signifier

        annotations = [
            Query[int],
            Query[str],
            Query[bool],
            Query[list[str]],
            Query[dict[str, int]],
        ]

        def extract_all():
            for ann in annotations:
                extract_signifier(ann)

        benchmark(extract_all)

    def test_is_optional(self, benchmark):
        """Benchmark is_optional function."""
        from typing import Optional

        from hatchway.types import is_optional

        annotations = [
            int,
            str | None,
            Optional[str],
            int | None,
            list[str] | None,
        ]

        def check_all():
            for ann in annotations:
                is_optional(ann)

        benchmark(check_all)


class TestRequestProcessingOverhead:
    """Benchmark overall request processing overhead."""

    def test_minimal_view_overhead(self, benchmark):
        """Benchmark minimal view (measure framework overhead)."""

        @api_view.get
        def minimal_view(request):
            return {"status": "ok"}

        factory = RequestFactory()
        request = factory.get("/test/")

        result = benchmark(minimal_view, request)
        assert result.status_code == 200

    def test_no_validation_overhead(self, benchmark):
        """Benchmark view without type validation (simple types)."""

        @api_view.get
        def no_validation_view(request, value: str):
            return {"value": value}

        factory = RequestFactory()
        request = factory.get("/test/?value=42")

        result = benchmark(no_validation_view, request)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_full_stack_overhead(self, benchmark):
        """Benchmark full request processing stack."""
        from .factories import PostFactory

        post = PostFactory()

        from api.schemas import PostSchema

        @api_view.get
        def full_view(request, id: int, include_meta: bool = False) -> PostSchema:
            from api.models import Post

            return Post.objects.get(id=id)

        factory = RequestFactory()
        request = factory.get(f"/test/?include_meta=true")

        result = benchmark(full_view, request, id=post.id)
        assert result.status_code == 200


class TestValidationPerformance:
    """Benchmark validation performance."""

    def test_validation_success(self, benchmark):
        """Benchmark successful validation."""

        class StrictSchema(Schema):
            email: str
            age: int
            name: str

        @api_view.post
        def test_view(request, data: StrictSchema):
            return {"ok": True}

        factory = RequestFactory()
        import json

        request = factory.post(
            "/test/",
            data=json.dumps({"email": "test@example.com", "age": 30, "name": "Test"}),
            content_type="application/json",
        )

        result = benchmark(test_view, request)
        assert result.status_code == 200

    def test_validation_failure(self, benchmark):
        """Benchmark validation failure (error path)."""

        class StrictSchema(Schema):
            email: str
            age: int
            name: str

        @api_view.post
        def test_view(request, data: StrictSchema):
            return {"ok": True}

        factory = RequestFactory()
        import json

        request = factory.post(
            "/test/",
            data=json.dumps({"email": "invalid", "age": "not a number"}),
            content_type="application/json",
        )

        result = benchmark(test_view, request)
        assert result.status_code == 400


class TestResponseFormattingPerformance:
    """Benchmark response formatting."""

    def test_dict_response(self, benchmark):
        """Benchmark dict response formatting."""

        @api_view.get
        def test_view(request) -> dict:
            return {"a": 1, "b": "test", "c": [1, 2, 3], "d": {"nested": True}}

        factory = RequestFactory()
        request = factory.get("/test/")

        result = benchmark(test_view, request)
        assert result.status_code == 200

    def test_list_response(self, benchmark):
        """Benchmark list response formatting."""

        @api_view.get
        def test_view(request) -> list[dict]:
            return [{"id": i, "name": f"item{i}"} for i in range(100)]

        factory = RequestFactory()
        request = factory.get("/test/")

        result = benchmark(test_view, request)
        assert result.status_code == 200

    @pytest.mark.django_db
    def test_schema_response(self, benchmark):
        """Benchmark schema response formatting."""
        from .factories import create_posts

        posts = create_posts(count=20, with_comments=False)

        from api.schemas import PostListSchema

        @api_view.get
        def test_view(request) -> list[PostListSchema]:
            from api.models import Post

            return list(Post.objects.all()[:20])

        factory = RequestFactory()
        request = factory.get("/test/")

        result = benchmark(test_view, request)
        assert result.status_code == 200
