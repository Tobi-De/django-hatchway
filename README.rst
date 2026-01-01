django-hatchway
===============

> [!IMPORTANT]
> Fork of https://github.com/andrewgodwin/django-hatchway

Hatchway is an API framework inspired by the likes of FastAPI, but while trying
to keep API views as much like standard Django views as possible.

It was built for, and extracted from, `Takahē <https://github.com/jointakahe/takahe>`_;
if you want to see an example of it being used, browse its
`api app <https://github.com/jointakahe/takahe/tree/main/api>`_.


Installation
------------

Install Hatchway from PyPI::

    pip install django-hatchway

And add it to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "hatchway",
    ]


Usage
-----

To make a view an API endpoint, you should write a standard function-based
view, and decorate it with ``@api_view.get``, ``@api_view.post`` or similar:

.. code-block:: python

    from hatchway import api_view

    @api_view.get
    def my_api_endpoint(request, id: int, limit: int = 100) -> list[str]:
        ...


The types of your function arguments matter; Hatchway will use them to work out
where to get their values from and how to parse them. All the standard Python
types are supported, plus structured Schema models based on ``msgspec.Struct``
(which ideally you should build based on the ``hatchway.Schema`` base class,
as it understands how to load things from Django model instances).

Your return type also matters - this is what Hatchway uses to work out how to
format/validate the return value. You can leave it off, or set it to ``Any``,
if you don't want any return validation.

URL Patterns
~~~~~~~~~~~~

You add API views in your ``urls.py`` file like any other view:

.. code-block:: python

    urlpatterns = [
        ...
        path("api/test/", my_api_endpoint),
    ]

The view will only accept the method it was decorated with (e.g. ``GET`` for
``api_view.get``).

If you want to have two or more views on the same URL but responding to
different methods, use Hatchway's ``methods`` object:

.. code-block:: python

    from hatchway import methods

    urlpatterns = [
        ...
        path(
            "api/post/<id>/",
            methods(
                get=posts.post_get,
                delete=posts.posts_delete,
            ),
        ),
    ]


Argument Sourcing
~~~~~~~~~~~~~~~~~

There are four places that input arguments can be sourced from:

* **Path**: The URL of the view, as provided via kwargs from the URL resolver
* **Query**: Query parameters (``request.GET``)
* **Body**: The body of a request, in either JSON, formdata, or multipart format
* **File**: Uploaded files, as part of a multipart body

By default, Hatchway will pull arguments from these sources:

* Standard Python singular types (``int``, ``str``, ``float``, etc.): Path first, and then Query
* Python collection types (``list[int]``, etc.): Query only, with implicit list conversion of either one or multiple values
* ``hatchway.Schema`` subclasses (msgspec Struct models): Body only (see Model Sourcing below)
* ``django.core.files.File``: File only

You can override where Hatchway pulls an argument from by using one of the
``Path``, ``Query``, ``Body``, ``File``, ``QueryOrBody``, ``PathOrQuery``,
or ``BodyDirect`` annotations:

.. code-block:: python

    from hatchway import api_view, Path, QueryOrBody

    @api_view.post
    def my_api_endpoint(request, id: Path[int], limit: QueryOrBody[int] = 100) -> dict:
        ...

While ``Path``, ``Query``, ``Body`` and ``File`` force the argument to be
picked from only that source, there are some more complex ones in there:

* ``PathOrQuery`` first tries the Path, then tries the Query (the default for simple types)
* ``QueryOrBody`` first tries the Query, then tries the Body
* ``BodyDirect`` forces top-level population of a model - see Model Sourcing, below.

Model Sourcing
~~~~~~~~~~~~~~

When you define a ``hatchway.Schema`` subclass (msgspec Struct model),
Hatchway will presume that it should pull it from the POST/PUT/etc. body.

How it pulls it depends on how many body-sourced arguments you have:

* If you just have one, it will feed it the top-level keys in the body data as
  its internal values.

* If you have more than one, it will look for its data in a sub-key named the
  same as the argument name.

For example, this function has two body-sourced things (one implicit, one explicit):

.. code-block:: python

    @api_view.post
    def my_api_endpoint(request, thing: schemas.MyInputSchema, limit: Body[int] = 100):
        ...

This means Hatchway will feed the ``schemas.MyInputSchema`` model whatever it
finds under the ``thing`` key in the request body as its input, and ``limit``
will come from the ``limit`` key.

If ``limit`` wasn't specified, then there would be only one body-sourced item,
and Hatchway would feed ``schemas.MyInputSchema`` the entire request body as
its input.

You can force a schema subclass to be fed the entire request body by using the
``BodyDirect[MySchemaClass]`` annotation on its type.

Return Values
~~~~~~~~~~~~~

The return value of an API view, if provided, is used to validate and coerce
the type of the response:

.. code-block:: python

    @api_view.delete
    def my_api_endpoint(request) -> int:
        ...

It can be either a normal Python type, or a ``hatchway.Schema`` subclass. If
it is a Schema subclass, the response will be fed to it for coercion, and ORM
objects are supported - returning a model instance, a dict with the model
instance values, or an instance of the schema are all equivalent.

A typechecker will honour these too, so we generally recommend returning
instances of your Schema so that your entire view benefits from typechecking,
rather than relying on the coercion. You'll get typechecking in your Schema
subclass constructors, and then typechecking that you're always returnining
the right things from the view.

You can also use generics like ``list[MySchemaClass]`` or
``dict[str, MySchemaClass]`` as a response type; generally, anything msgspec
supports, we do as well.

Adding Headers/Status Codes to the Response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to do more to your response than just sling some data back at your
client, you can return an ApiResponse object instead of a plain value:

.. code-block:: python

    from hatchway import api_view, ApiResponse

    @api_view.delete
    def my_api_endpoint(request) -> ApiResponse[int]:
        ...
        return ApiResponse(42, headers={"X-Safe-Delete": "no"})

``ApiResponse`` is a standard Django ``HTTPResponse`` subclass, so accepts
almost all of the same arguments, and has most of the same methods. Just don't
edit its ``.content`` value; if you want to mutate the data you passed into
it, that is stored in ``.data``.

Note that we also changed the return type of the view so that it would pass
typechecking; ``ApiResponse`` accepts any response type as its argument and
passes it through to the same validation layer.

Auto-Collections
~~~~~~~~~~~~~~~~

Hatchway allows you to say that Schema subclasses can pull their values from
individual query parameters or body values; these are normally flat strings,
though, unless you're looking at a JSON-encoded body, or multiple repeated
query parameters.

However, it will respect the use of ``name[]`` to make lists, and ``name[key]``
to make dicts. Some examples:

* A ``a=Query[list[int]]`` argument will see ``url?a=1`` as ``[1]``,
  ``url?a=1&a=2`` as ``[1, 2]``, and ``url?a[]=1&a[]=2`` as ``[1, 2]``.

* A ``b=Body[dict[str, int]]`` argument will correctly accept the POST data
  ``b[age]=30&b[height]=180`` and give you ``{"age": 30, "height": 180}``.

These will also work in JSON bodies too, though of course you don't need them
there; nevertheless, they still work for compatibility reasons.

Authentication & Permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hatchway includes built-in authentication and permissions support that integrates
with Django's standard authentication system.

Basic Authentication
++++++++++++++++++++

To require authentication for a view, use the ``auth=True`` parameter:

.. code-block:: python

    from hatchway import api_view

    @api_view.get(auth=True)
    def user_profile(request) -> dict:
        return {
            "user_id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
        }

This endpoint will:

* Return a **401 Unauthorized** response with ``{"error": "authentication_required"}``
  if the user is not authenticated
* Accept both **session authentication** (Django's standard session middleware)
  and **token authentication** (via ``Authorization: Token <token>`` header)

Permission Checking
+++++++++++++++++++

You can require specific Django permissions using the ``permissions`` parameter:

.. code-block:: python

    from hatchway import api_view

    @api_view.post(auth=True, permissions=["blog.add_post"])
    def create_post(request, data: PostCreateSchema) -> PostSchema:
        post = Post.objects.create(author=request.user, **data.dict())
        return post

This endpoint will:

* Return a **401 Unauthorized** response if the user is not authenticated
* Return a **403 Forbidden** response with ``{"error": "permission_denied"}``
  if the user lacks the required permission
* Allow the request to proceed if the user has the ``blog.add_post`` permission

You can require multiple permissions by passing a list. All permissions must be
granted for the request to succeed.

Token Authentication
++++++++++++++++++++

Hatchway includes a built-in token authentication model. Tokens can be created
via a management command or through an API endpoint.

**Creating Tokens via Management Command**

.. code-block:: bash

    python manage.py create_token username --days 365 --description "API access"

**Creating Tokens via API Endpoint**

You can create an API endpoint for users to obtain their own tokens:

.. code-block:: python

    from hatchway import api_view, ApiError, Schema
    from hatchway.models import AuthToken
    from django.contrib.auth import authenticate

    class LoginRequest(Schema):
        username: str
        password: str

    class TokenResponse(Schema):
        token: str
        expires_at: str

    @api_view.post
    def obtain_token(request, credentials: LoginRequest) -> TokenResponse:
        # Authenticate the user
        user = authenticate(
            username=credentials.username,
            password=credentials.password
        )

        if user is None:
            raise ApiError(401, "Invalid credentials")

        # Create a token for the user
        token = AuthToken.create_token(
            user=user,
            days_valid=365,
            description="API access via login"
        )

        return TokenResponse(
            token=token.token,
            expires_at=token.expires.isoformat()
        )

This will output a secure token that can be used in API requests:

.. code-block:: bash

    curl -H "Authorization: Token <token>" https://example.com/api/endpoint/

Tokens can be managed through the Django admin interface. They include:

* Automatic expiration (default: 365 days)
* Optional descriptions for tracking token usage
* Association with a specific user account

Custom Authentication Backends
+++++++++++++++++++++++++++++++

By default, Hatchway tries both session and token authentication. You can
restrict to specific backends by passing a list of backend class paths:

.. code-block:: python

    @api_view.get(auth=["hatchway.auth.TokenAuthBackend"])
    def api_only_endpoint(request) -> dict:
        # This endpoint only accepts token authentication, not sessions
        return {"message": "Token auth only", "user_id": request.user.id}

Available backends:

* ``hatchway.auth.SessionAuthBackend`` - Django session authentication
* ``hatchway.auth.TokenAuthBackend`` - Token-based authentication

You can create custom authentication backends by implementing the ``AuthBackend``
protocol (a class with an ``authenticate(request)`` method that returns a user
or ``None``).

Configuration
+++++++++++++

Add to your Django ``settings.py`` to customize authentication backends:

.. code-block:: python

    HATCHWAY_AUTH_BACKENDS = [
        'hatchway.auth.SessionAuthBackend',
        'hatchway.auth.TokenAuthBackend',
    ]

These backends are tried in sequence; the first one to return a user wins.

OpenAPI Documentation
~~~~~~~~~~~~~~~~~~~~~

Hatchway provides automatic OpenAPI 3.0 specification generation from your API views.
The OpenAPI spec is generated by introspecting your URL patterns and extracting
information from type hints, decorators, and Schema models.

Basic Setup
+++++++++++

To add OpenAPI documentation to your API:

.. code-block:: python

    from django.urls import path
    from hatchway import methods
    from hatchway.openapi import OpenAPIConfig, create_openapi_views
    from . import views

    # Define your API endpoints
    api_endpoints = [
        path("posts/", views.post_list, name="post_list"),
        path("posts/create/", views.post_create, name="post_create"),
        path("posts/<int:id>/", methods(
            get=views.post_detail,
            patch=views.post_update,
            delete=views.post_delete,
        )),
    ]

    # Configure OpenAPI
    openapi_config = OpenAPIConfig(
        title="My API",
        version="1.0.0",
        description="My awesome API built with Hatchway",
        contact={"name": "Support", "email": "support@example.com"},
        license={"name": "MIT"},
        servers=[{"url": "http://localhost:8000/api"}],
        tags=[
            {"name": "posts", "description": "Blog post management"},
        ],
    )

    # Generate OpenAPI views
    openapi_json, openapi_yaml, swagger_ui = create_openapi_views(
        openapi_config, api_endpoints
    )

    # Add documentation endpoints
    urlpatterns = [
        path("docs/", swagger_ui, name="swagger_ui"),
        path("openapi.json", openapi_json, name="openapi_json"),
        path("openapi.yaml", openapi_yaml, name="openapi_yaml"),
    ] + api_endpoints

This will create three endpoints:

* ``/docs/`` - Interactive Swagger UI documentation
* ``/openapi.json`` - OpenAPI spec in JSON format
* ``/openapi.yaml`` - OpenAPI spec in YAML format

What Gets Generated
+++++++++++++++++++

The OpenAPI generator automatically creates:

**Parameters**: Extracted from function arguments and type hints

* Path parameters from URL patterns (``<int:id>`` → path parameter)
* Query parameters from ``Query[T]``, ``PathOrQuery[T]``, ``QueryOrBody[T]`` annotations
* Request body schemas from ``Body[T]``, ``BodyDirect[T]``, or Schema models
* File upload parameters from ``File[T]`` annotations
* Default values and required status from function signatures

**Schemas**: Converted from ``msgspec.Struct`` models

* All ``hatchway.Schema`` subclasses are converted to OpenAPI schemas
* Validation constraints (min/max, length, pattern) from ``msgspec.Meta`` are preserved
* Nested schemas, lists, dicts, unions, and optional types are supported
* Generates proper ``$ref`` references for reusable schemas

**Responses**: Generated from return type hints

* Success response schema from the function's return type
* Automatic status code selection (201 for POST, 200 for others)
* Standard error responses (400 validation, 401 authentication, 403 permission)
* Supports ``ApiResponse[T]`` for custom status codes

**Security**: Detected from authentication decorators

* Operations with ``auth=True`` include security requirements
* Operations with ``permissions=[]`` include permission requirements
* Security schemes can be customized in ``OpenAPIConfig``

Schema Validation
++++++++++++++++++

When using ``msgspec.Struct`` with validation constraints, they are automatically
included in the OpenAPI schema:

.. code-block:: python

    from typing import Annotated
    from hatchway import Schema, Meta

    class UserCreateSchema(Schema):
        username: Annotated[str, Meta(min_length=3, max_length=50)]
        email: str
        age: Annotated[int, Meta(ge=18, le=120)]
        bio: Annotated[str, Meta(max_length=500)] | None = None

This generates an OpenAPI schema with:

* ``username``: string with minLength=3, maxLength=50
* ``email``: string (required)
* ``age``: integer with minimum=18, maximum=120
* ``bio``: string with maxLength=500 (optional, nullable)

Authentication in OpenAPI
++++++++++++++++++++++++++

The OpenAPI spec automatically includes security definitions for authenticated
endpoints. You can customize the security schemes in your config:

.. code-block:: python

    openapi_config = OpenAPIConfig(
        title="My API",
        version="1.0.0",
        # Add security schemes
        components={
            "securitySchemes": {
                "TokenAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "description": "Token authentication using 'Token <token>' format"
                },
                "SessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "sessionid",
                    "description": "Django session authentication"
                }
            }
        },
    )

Operations decorated with ``@api_view.get(auth=True)`` will automatically include
security requirements in the generated OpenAPI spec.
