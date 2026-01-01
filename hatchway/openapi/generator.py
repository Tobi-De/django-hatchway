"""
OpenAPI specification generator for Hatchway.

This module introspects Django URL patterns and generates OpenAPI 3.0 specifications.
"""

from __future__ import annotations

import inspect
import re
from typing import Any

from django.urls import URLPattern, URLResolver
from django.urls.resolvers import RoutePattern
from openapi_spec_models import (
    Components,
    Info,
    OpenAPI,
    OpenAPIMediaType,
    OpenAPIResponse,
    Operation,
    Parameter,
    PathItem,
    Reference,
    RequestBody,
    Schema,
    SecurityRequirement,
    Server,
)

from ..constants import InputSource
from ..urls import Methods
from ..view import ApiView
from .config import OpenAPIConfig
from .schema import collect_schema_definitions, get_openapi_type


# Mapping of camelCase OpenAPI keys to snake_case Schema field names
OPENAPI_TO_SCHEMA_FIELD_MAP = {
    "type": "type",
    "format": "format",
    "title": "title",
    "description": "description",
    "default": "default",
    "deprecated": "deprecated",
    "readOnly": "read_only",
    "writeOnly": "write_only",
    "example": "example",
    "examples": "examples",
    "externalDocs": "external_docs",
    "multipleOf": "multiple_of",
    "maximum": "maximum",
    "exclusiveMaximum": "exclusive_maximum",
    "minimum": "minimum",
    "exclusiveMinimum": "exclusive_minimum",
    "maxLength": "max_length",
    "minLength": "min_length",
    "pattern": "pattern",
    "maxItems": "max_items",
    "minItems": "min_items",
    "uniqueItems": "unique_items",
    "maxProperties": "max_properties",
    "minProperties": "min_properties",
    "required": "required",
    "enum": "enum",
    "const": "const",
    "allOf": "all_of",
    "oneOf": "one_of",
    "anyOf": "any_of",
    "not": "schema_not",
    "items": "items",
    "properties": "properties",
    "additionalProperties": "additional_properties",
    "patternProperties": "pattern_properties",
    "propertyNames": "property_names",
    "if": "schema_if",
    "then": "then",
    "else": "schema_else",
    "dependentSchemas": "dependent_schemas",
    "prefixItems": "prefix_items",
    "contains": "contains",
    "unevaluatedItems": "unevaluated_items",
    "unevaluatedProperties": "unevaluated_properties",
    "discriminator": "discriminator",
    "xml": "xml",
    # Note: nullable is not a standard field in Schema dataclass from litestar
}


def dict_to_schema(openapi_dict: dict[str, Any]) -> Schema:
    """
    Convert an OpenAPI schema dictionary (camelCase keys) to a Schema dataclass instance.

    Args:
        openapi_dict: Dictionary with OpenAPI schema keys (camelCase)

    Returns:
        Schema dataclass instance
    """
    # Convert camelCase keys to snake_case field names
    schema_kwargs = {}
    for camel_key, value in openapi_dict.items():
        if camel_key in OPENAPI_TO_SCHEMA_FIELD_MAP:
            snake_key = OPENAPI_TO_SCHEMA_FIELD_MAP[camel_key]
            schema_kwargs[snake_key] = value
        elif camel_key == "nullable":
            # nullable is handled differently in litestar - skip it for now
            continue
        else:
            # Unknown key - log warning but skip
            pass

    return Schema(**schema_kwargs)


class OpenAPIGenerator:
    """
    Generate OpenAPI specification from Django URL patterns containing Hatchway views.
    """

    def __init__(self, config: OpenAPIConfig):
        """
        Initialize the OpenAPI generator.

        Args:
            config: OpenAPI configuration
        """
        self.config = config
        self.schemas: dict[str, dict[str, Any]] = {}

    def generate(self, urlpatterns, base_path: str = "") -> OpenAPI:
        """
        Generate OpenAPI specification from URL patterns.

        Args:
            urlpatterns: Django URL patterns to introspect
            base_path: Base path prefix for all routes

        Returns:
            Complete OpenAPI specification object
        """
        # Process URL patterns
        paths: dict[str, PathItem] = {}
        self._process_urlpatterns(urlpatterns, base_path, paths)

        # Build components
        components_dict = self.config._get_default_components()

        # Add collected schemas
        if self.schemas:
            if "schemas" not in components_dict:
                components_dict["schemas"] = {}
            components_dict["schemas"].update(self.schemas)

        # Build info object
        info = Info(
            title=self.config.title,
            version=self.config.version,
            description=self.config.description,
            terms_of_service=self.config.terms_of_service,
            contact=self.config.contact,
            license=self.config.license,
        )

        # Build servers
        servers = [Server(**s) if isinstance(s, dict) else s for s in self.config.servers]

        # Build OpenAPI object
        openapi = OpenAPI(
            openapi="3.0.3",
            info=info,
            servers=servers,
            paths=paths,
            components=Components(**components_dict) if components_dict else None,
            tags=self.config.tags,
            external_docs=self.config.external_docs,
            security=self.config.security,
        )

        return openapi

    def _process_urlpatterns(
        self, urlpatterns, prefix: str, paths: dict[str, PathItem]
    ) -> None:
        """
        Recursively process URL patterns to extract Hatchway views.

        Args:
            urlpatterns: Django URL patterns
            prefix: Current path prefix
            paths: Dictionary to collect path operations
        """
        for pattern in urlpatterns:
            if isinstance(pattern, URLResolver):
                # Recursively process included URLconfs
                new_prefix = prefix + str(pattern.pattern)
                self._process_urlpatterns(pattern.url_patterns, new_prefix, paths)
            elif isinstance(pattern, URLPattern):
                # Process individual URL pattern
                path = prefix + str(pattern.pattern)
                self._process_url_pattern(pattern, path, paths)

    def _process_url_pattern(
        self, pattern: URLPattern, path: str, paths: dict[str, PathItem]
    ) -> None:
        """
        Process a single URL pattern and add its operations to paths.

        Args:
            pattern: Django URL pattern
            path: Full path string
            paths: Dictionary to collect path operations
        """
        callback = pattern.callback

        # Convert Django path syntax to OpenAPI path syntax
        openapi_path = self._convert_path_to_openapi(path)

        # Handle Methods wrapper (multi-method endpoint)
        if isinstance(callback, Methods):
            operations = {}
            for method_name, view in callback.callables.items():
                if isinstance(view, ApiView):
                    operation = self._generate_operation(view, pattern)
                    if operation:
                        operations[method_name] = operation

            if operations:
                if openapi_path in paths:
                    # Merge with existing path item
                    existing = paths[openapi_path]
                    for method, op in operations.items():
                        setattr(existing, method, op)
                else:
                    paths[openapi_path] = PathItem(**operations)

        # Handle ApiView
        elif isinstance(callback, ApiView):
            method = (callback.method or "get").lower()
            operation = self._generate_operation(callback, pattern)
            if operation:
                if openapi_path in paths:
                    # Add to existing path item
                    setattr(paths[openapi_path], method, operation)
                else:
                    paths[openapi_path] = PathItem(**{method: operation})

    def _convert_path_to_openapi(self, django_path: str) -> str:
        """
        Convert Django path syntax to OpenAPI path syntax.

        Examples:
            posts/<int:id>/ -> /posts/{id}/
            posts/<slug:slug>/ -> /posts/{slug}/
        """
        # Convert Django path parameters to OpenAPI format
        openapi_path = re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", django_path)

        # Ensure path starts with /
        if not openapi_path.startswith("/"):
            openapi_path = "/" + openapi_path

        return openapi_path

    def _generate_operation(
        self, view: ApiView, pattern: URLPattern
    ) -> Operation | None:
        """
        Generate OpenAPI operation object from an ApiView.

        Args:
            view: The ApiView instance
            pattern: The URL pattern

        Returns:
            OpenAPI operation object or None if generation fails
        """
        # Extract summary and description from docstring
        summary = None
        description = None
        if view.view.__doc__:
            lines = view.view.__doc__.strip().split("\n")
            summary = lines[0].strip()
            if len(lines) > 1:
                description = "\n".join(line.strip() for line in lines[1:]).strip()

        # Generate operation ID from view name
        operation_id = view.view_name

        # Add parameters (path and query)
        parameters = self._generate_parameters(view, pattern)

        # Add request body (for POST, PUT, PATCH)
        request_body = self._generate_request_body(view)

        # Add responses
        responses = self._generate_responses(view)

        # Add security requirements if auth is enabled
        security = self._generate_security(view) if view.auth else None

        return Operation(
            summary=summary,
            description=description,
            operation_id=operation_id,
            parameters=parameters if parameters else None,
            request_body=request_body,
            responses=responses,
            security=security,
        )

    def _generate_parameters(
        self, view: ApiView, pattern: URLPattern
    ) -> list[Parameter]:
        """
        Generate OpenAPI parameter objects for path and query parameters.

        Args:
            view: The ApiView instance
            pattern: The URL pattern

        Returns:
            List of OpenAPI parameter objects
        """
        parameters = []

        # Extract path parameter names from the pattern
        path_params = set()
        if isinstance(pattern.pattern, RoutePattern):
            route = str(pattern.pattern)
            path_params = set(re.findall(r"<(?:\w+:)?(\w+)>", route))

        for param_name, sources in view.sources.items():
            param_type = view.input_types.get(param_name)
            if not param_type:
                continue

            # Get default value from function signature
            sig = inspect.signature(view.view)
            default_value = inspect.Parameter.empty
            if param_name in sig.parameters:
                default_value = sig.parameters[param_name].default

            # Determine if parameter is required
            required = default_value == inspect.Parameter.empty

            # Convert type to OpenAPI schema
            param_schema_dict = get_openapi_type(param_type)

            # Handle $ref case (use Reference instead of Schema)
            if "$ref" in param_schema_dict:
                param_schema = Reference(ref=param_schema_dict["$ref"])
            else:
                param_schema = dict_to_schema(param_schema_dict)
                # Add default value if present
                if default_value != inspect.Parameter.empty and default_value is not None:
                    param_schema.default = default_value

            # Path parameters
            if InputSource.path in sources and param_name in path_params:
                parameters.append(
                    Parameter(
                        name=param_name,
                        param_in="path",
                        required=True,
                        schema=param_schema,
                    )
                )

            # Query parameters
            elif InputSource.query in sources or InputSource.query_list in sources:
                parameters.append(
                    Parameter(
                        name=param_name,
                        param_in="query",
                        required=required,
                        schema=param_schema,
                    )
                )

        return parameters

    def _generate_request_body(self, view: ApiView) -> RequestBody | None:
        """
        Generate OpenAPI request body object for body parameters.

        Args:
            view: The ApiView instance

        Returns:
            OpenAPI request body object or None
        """
        body_params = {}
        has_files = False

        for param_name, sources in view.sources.items():
            param_type = view.input_types.get(param_name)
            if not param_type:
                continue

            # Check for body parameters
            if InputSource.body in sources or InputSource.body_direct in sources:
                body_params[param_name] = param_type
                # Collect schema definitions
                collect_schema_definitions(param_type, self.schemas)

            # Check for file parameters
            elif InputSource.file in sources:
                has_files = True
                body_params[param_name] = param_type

        if not body_params:
            return None

        # Determine content type
        if has_files:
            # Multipart form data
            properties = {}
            required = []

            sig = inspect.signature(view.view)
            for param_name, param_type in body_params.items():
                if InputSource.file in view.sources.get(param_name, []):
                    properties[param_name] = Schema(type="string", format="binary")
                else:
                    schema_dict = get_openapi_type(param_type)
                    if "$ref" in schema_dict:
                        properties[param_name] = Reference(ref=schema_dict["$ref"])
                    else:
                        properties[param_name] = dict_to_schema(schema_dict)

                # Check if required
                if param_name in sig.parameters:
                    default_value = sig.parameters[param_name].default
                    if default_value == inspect.Parameter.empty:
                        required.append(param_name)

            schema = Schema(
                type="object",
                properties=properties,
                required=required if required else None,
            )

            return RequestBody(
                required=True,
                content={"multipart/form-data": OpenAPIMediaType(schema=schema)},
            )
        else:
            # JSON body
            # Check if there's a single body_direct parameter
            if len(body_params) == 1:
                param_name, param_type = next(iter(body_params.items()))
                if InputSource.body_direct in view.sources.get(param_name, []):
                    # Use the schema directly
                    schema_dict = get_openapi_type(param_type)
                    if "$ref" in schema_dict:
                        schema = Reference(ref=schema_dict["$ref"])
                    else:
                        schema = dict_to_schema(schema_dict)
                    return RequestBody(
                        required=True,
                        content={"application/json": OpenAPIMediaType(schema=schema)},
                    )

            # Multiple body parameters - wrap in object
            properties = {}
            required = []

            sig = inspect.signature(view.view)
            for param_name, param_type in body_params.items():
                schema_dict = get_openapi_type(param_type)
                if "$ref" in schema_dict:
                    properties[param_name] = Reference(ref=schema_dict["$ref"])
                else:
                    properties[param_name] = dict_to_schema(schema_dict)

                # Check if required
                if param_name in sig.parameters:
                    default_value = sig.parameters[param_name].default
                    if default_value == inspect.Parameter.empty:
                        required.append(param_name)

            schema = Schema(
                type="object",
                properties=properties,
                required=required if required else None,
            )

            return RequestBody(
                required=True,
                content={"application/json": OpenAPIMediaType(schema=schema)},
            )

    def _generate_responses(self, view: ApiView) -> dict[str, OpenAPIResponse]:
        """
        Generate OpenAPI response objects.

        Args:
            view: The ApiView instance

        Returns:
            Dictionary of status code -> response object
        """
        responses = {}

        # Determine status code based on HTTP method
        method = (view.method or "get").lower()
        status_code = "201" if method == "post" else "200"

        # Success response
        if view.output_type:
            # Collect schema definitions from output type
            collect_schema_definitions(view.output_type, self.schemas)

            response_schema_dict = get_openapi_type(view.output_type)
            if "$ref" in response_schema_dict:
                response_schema = Reference(ref=response_schema_dict["$ref"])
            else:
                response_schema = dict_to_schema(response_schema_dict)

            responses[status_code] = OpenAPIResponse(
                description="Successful response",
                content={"application/json": OpenAPIMediaType(schema=response_schema)},
            )
        else:
            # No output type specified
            responses[status_code] = OpenAPIResponse(description="Successful response")

        # Add common error responses
        error_schema = Schema(
            type="object",
            properties={
                "error": Schema(type="string"),
                "error_details": Schema(type="array", items=Schema()),
            },
        )

        responses["400"] = OpenAPIResponse(
            description="Validation error",
            content={"application/json": OpenAPIMediaType(schema=error_schema)},
        )

        if view.auth:
            auth_error_schema = Schema(
                type="object",
                properties={"error": Schema(type="string")},
            )
            responses["401"] = OpenAPIResponse(
                description="Authentication required",
                content={"application/json": OpenAPIMediaType(schema=auth_error_schema)},
            )

        if view.permissions:
            perm_error_schema = Schema(
                type="object",
                properties={"error": Schema(type="string")},
            )
            responses["403"] = OpenAPIResponse(
                description="Permission denied",
                content={"application/json": OpenAPIMediaType(schema=perm_error_schema)},
            )

        return responses

    def _generate_security(self, view: ApiView) -> list[SecurityRequirement]:
        """
        Generate security requirements for an operation.

        Args:
            view: The ApiView instance

        Returns:
            List of security requirement dictionaries
        """
        # Use the security scheme names defined in the config
        # Allow either TokenAuth or SessionAuth
        # SecurityRequirement is a type alias for dict[str, list[str]]
        return [
            {"TokenAuth": []},
            {"SessionAuth": []},
        ]
