"""
Factory definitions for creating test data.
"""

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class PostFactory(DjangoModelFactory):
    class Meta:
        model = "api.Post"
        skip_postgeneration_save = True

    title = factory.Faker("sentence", nb_words=6)
    content = factory.Faker("paragraphs", nb=3)
    author = factory.SubFactory(UserFactory)
    published = factory.Faker("boolean", chance_of_getting_true=70)
    tags = factory.LazyFunction(
        lambda: [fake.word() for _ in range(fake.random_int(min=0, max=5))]
    )

    @factory.post_generation
    def content_as_text(obj, create, extracted, **kwargs):
        """Convert content list to text."""
        if isinstance(obj.content, list):
            obj.content = "\n\n".join(obj.content)
            if create:
                obj.save()


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = "api.Comment"

    post = factory.SubFactory(PostFactory)
    author_name = factory.Faker("name")
    content = factory.Faker("paragraph")
    rating = factory.Faker("random_int", min=0, max=5)


# Batch factories for creating large datasets
def create_posts(count=100, with_comments=True):
    """Create a batch of posts with optional comments."""
    user = UserFactory()
    posts = PostFactory.create_batch(count, author=user)

    if with_comments:
        for post in posts:
            # Random number of comments per post
            comment_count = fake.random_int(min=0, max=10)
            CommentFactory.create_batch(comment_count, post=post)

    return posts


def create_large_dataset():
    """Create a large dataset for stress testing."""
    users = UserFactory.create_batch(10)
    posts = []

    for user in users:
        user_posts = PostFactory.create_batch(50, author=user)
        posts.extend(user_posts)

    for post in posts:
        comment_count = fake.random_int(min=0, max=20)
        CommentFactory.create_batch(comment_count, post=post)

    return {"users": users, "posts": posts}
