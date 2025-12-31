from datetime import datetime

from hatchway import Field, Schema


class PostSchema(Schema):
    """Schema for Post model - demonstrates ORM mode"""

    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime
    published: bool
    tags: list[str]
    comment_count: int  # Callable method will be auto-invoked


class PostListSchema(Schema):
    """Simplified schema for listing posts"""

    id: int
    title: str
    author_id: int
    created_at: datetime
    published: bool
    comment_count: int


class PostCreateSchema(Schema):
    """Schema for creating posts - demonstrates input validation"""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    author_id: int = Field(gt=0)
    published: bool = False
    tags: list[str] = []


class PostUpdateSchema(Schema):
    """Schema for updating posts - all fields optional"""

    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = Field(None, min_length=1)
    published: bool | None = None
    tags: list[str] | None = None


class CommentSchema(Schema):
    """Schema for Comment model"""

    id: int
    post_id: int
    author_name: str
    content: str
    created_at: datetime
    rating: int


class CommentCreateSchema(Schema):
    """Schema for creating comments"""

    author_name: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    rating: int = Field(ge=0, le=5, default=0)


class ErrorSchema(Schema):
    """Example error response schema"""

    error: str
    details: str | None = None


class PaginatedResponse(Schema):
    """Generic paginated response"""

    count: int
    next: str | None
    previous: str | None
    results: list[dict]
