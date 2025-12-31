import json
from collections.abc import Callable
from typing import Any, Optional, get_origin, get_type_hints

import msgspec
from django.core import files
from django.http import HttpRequest, HttpResponseNotAllowed, QueryDict
from django.http.multipartparser import MultiPartParser

from .auth import authenticate_request, get_backends
from .constants import InputSource
from .http import ApiError, ApiResponse
from .permissions import check_permissions, require_authentication
from .schema import convert_from_orm
from .types import (
    BodyDirectType,
    BodyType,
    FileType,
    PathOrQueryType,
    PathType,
    QueryOrBodyType,
    QueryType,
    acceptable_input,
    extract_output_type,
    extract_signifier,
    is_model_subclass,
    is_optional,
)


class ApiView:
    """
    A view 'wrapper' object that replaces the API view for anything further
    up the stack.

    Unlike Django's class-based views, we don't need an as_view pattern
    as we are careful never to write anything per-request to self.
    """

    csrf_exempt = True

    def __init__(
        self,
        view: Callable,
        input_types: dict[str, Any] | None = None,
        output_type: Any = None,
        implicit_lists: bool = True,
        method: str | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        self.view = view
        self.implicit_lists = implicit_lists
        self.view_name = getattr(view, "__name__", "unknown_view")
        self.method = method
        self.auth = auth
        self.permissions = permissions or []
        self.validate_output = validate_output
        # Extract input/output types from view annotations if we need to
        self.input_types = input_types
        if self.input_types is None:
            self.input_types = get_type_hints(view, include_extras=True)
            if "return" in self.input_types:
                del self.input_types["return"]
        self.output_type = output_type
        if self.output_type is None:
            try:
                self.output_type = extract_output_type(
                    get_type_hints(view, include_extras=True)["return"]
                )
            except KeyError:
                self.output_type = None
        self.compile()

    @classmethod
    def _create_method_decorator(
        cls,
        method: str,
        view: Callable | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        """Factory for creating HTTP method decorators."""
        if view is None:
            # Called with arguments: @api_view.get(auth=True)
            return lambda v: cls(
                view=v,
                method=method,
                auth=auth,
                permissions=permissions,
                validate_output=validate_output,
            )
        # Called without arguments: @api_view.get
        return cls(
            view=view,
            method=method,
            auth=auth,
            permissions=permissions,
            validate_output=validate_output,
        )

    @classmethod
    def get(
        cls,
        view: Callable | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        return cls._create_method_decorator(
            "get", view, auth, permissions, validate_output
        )

    @classmethod
    def post(
        cls,
        view: Callable | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        return cls._create_method_decorator(
            "post", view, auth, permissions, validate_output
        )

    @classmethod
    def put(
        cls,
        view: Callable | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        return cls._create_method_decorator(
            "put", view, auth, permissions, validate_output
        )

    @classmethod
    def patch(
        cls,
        view: Callable | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        return cls._create_method_decorator(
            "patch", view, auth, permissions, validate_output
        )

    @classmethod
    def delete(
        cls,
        view: Callable | None = None,
        auth: bool | list[str] = False,
        permissions: list[str] | None = None,
        validate_output: bool = True,
    ):
        return cls._create_method_decorator(
            "delete", view, auth, permissions, validate_output
        )

    @classmethod
    def sources_for_input(cls, input_type) -> tuple[list[InputSource], Any]:
        """
        Given a type that can appear as a request parameter type, returns
        what sources it can come from and its resolved type.
        """
        signifier, input_type = extract_signifier(input_type)
        origin_type = get_origin(input_type)
        collection_types = {list, set, tuple, frozenset}
        if signifier is QueryType:
            return ([InputSource.query], input_type)
        elif signifier is BodyType:
            return ([InputSource.body], input_type)
        elif signifier is BodyDirectType:
            if not is_model_subclass(input_type):
                raise ValueError(
                    "You cannot use BodyDirect on something that is not a Schema model"
                )
            return ([InputSource.body_direct], input_type)
        elif signifier is PathType:
            return ([InputSource.path], input_type)
        elif (
            signifier is FileType
            or input_type is files.File
            or is_optional(input_type)[1] is files.File
        ):
            return ([InputSource.file], input_type)
        elif signifier is QueryOrBodyType:
            return ([InputSource.query, InputSource.body], input_type)
        elif signifier is PathOrQueryType:
            return ([InputSource.path, InputSource.query], input_type)
        # Schema models are implicitly body
        elif is_model_subclass(input_type):
            return ([InputSource.body], input_type)
        # Collections only come from the query, with implicit list conversion
        elif input_type in collection_types or origin_type in collection_types:
            return ([InputSource.query_list], input_type)
        # Otherwise, we look in the path first and then the query
        else:
            return ([InputSource.path, InputSource.query], input_type)

    @classmethod
    def get_values(cls, data, use_square_brackets=True) -> dict[str, Any]:
        """
        Given a QueryDict or normal dict, returns data taking into account
        lists made by repeated values or by suffixing names with [].
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            # If it's a query dict with multiple values, make it a list
            if isinstance(data, QueryDict):
                values = data.getlist(key)
                if len(values) > 1:
                    value = values
            # If it is in dict-ish/list-ish syntax, adhere to that
            # TODO: Make this better handle badly formed keys
            if "[" in key and use_square_brackets:
                parts = key.split("[")
                target = result
                last_key = parts[0]
                for part in parts[1:]:
                    part = part.rstrip("]")
                    if not part:
                        target = target.setdefault(last_key, [])
                    else:
                        target = target.setdefault(last_key, {})
                        last_key = part
                if isinstance(target, list):
                    if isinstance(value, list):
                        target.extend(value)
                    else:
                        target.append(value)
                else:
                    target[last_key] = value
            else:
                result[key] = value
        return result

    def compile(self):
        self.sources: dict[str, list[InputSource]] = {}
        amount_from_body = 0
        model_dict = {}
        self.input_files = set()
        last_body_type = None
        # For each input item, work out where to pull it from
        for name, input_type in self.input_types.items():
            # Do some basic typechecking to stop things that aren't allowed
            if isinstance(input_type, type) and issubclass(input_type, HttpRequest):
                continue
            if not acceptable_input(input_type):
                # Strip away any singifiers for the error
                _, inner_type = extract_signifier(input_type)
                raise ValueError(
                    f"Input argument {name} has an unsupported type {inner_type}"
                )
            sources, model_type = self.sources_for_input(input_type)
            self.sources[name] = sources
            # Keep count of how many are pulling from the body
            if InputSource.body in sources:
                amount_from_body += 1
                last_body_type = model_type
            if InputSource.file in sources:
                self.input_files.add(name)
            else:
                model_dict[name] = (Optional[model_type], ...)
        # If there is just one thing pulling from the body and it's a Schema model,
        # signify that it's actually pulling from the body keys directly and
        # not a sub-dict
        if amount_from_body == 1:
            for name, sources in self.sources.items():
                if (
                    InputSource.body in sources
                    and isinstance(last_body_type, type)
                    and is_model_subclass(last_body_type)
                ):
                    self.sources[name] = [
                        x for x in sources if x != InputSource.body
                    ] + [InputSource.body_direct]
        # Turn all the main arguments into msgspec struct models
        try:
            # Build field list for msgspec.defstruct
            field_list = []
            for name, model_type in model_dict.items():
                if isinstance(model_type, tuple):
                    field_type = model_type[0]
                else:
                    field_type = model_type
                field_list.append((name, Optional[field_type]))

            self.input_model = msgspec.defstruct(f"{self.view_name}_input", field_list)
        except (RuntimeError, TypeError) as e:
            raise ValueError(
                f"One or more inputs on view {self.view_name} have a bad configuration: {e}"
            )
        if self.output_type is not None:
            self.output_model = msgspec.defstruct(
                f"{self.view_name}_output", [("value", self.output_type)]
            )

    def __call__(self, request: HttpRequest, *args, **kwargs):
        """
        Entrypoint when this is called as a view.
        """
        # Do a method check if we have one set
        if self.method and self.method.upper() != request.method:
            return HttpResponseNotAllowed([self.method])

        # Authentication and permission checking
        if self.auth or self.permissions:
            # Get backends: pass list if custom, None for defaults
            backend_paths = self.auth if isinstance(self.auth, list) else None
            backends = get_backends(backend_paths)

            # Authenticate
            user, backend_name = authenticate_request(request, backends)
            if user is not None:
                request.user = user

            # Check if auth required
            if self.auth:
                success, error = require_authentication(user)
                if not success:
                    return ApiResponse({"error": error}, status=401, finalize=True)

            # Check permissions
            if self.permissions:
                success, error = check_permissions(user, self.permissions)
                if not success:
                    status = 401 if error == "authentication_required" else 403
                    return ApiResponse({"error": error}, status=status, finalize=True)

        view_kwargs = {}

        if self.sources or self.input_files:
            query_values = self.get_values(request.GET)
            body_values = self.get_values(request.POST)
            files_values = self.get_values(request.FILES)
            # If it's a PUT or PATCH method, work around Django not handling FILES
            # or POST on those requests
            if request.method in ["PATCH", "PUT"]:
                if request.content_type == "multipart/form-data":
                    POST, FILES = MultiPartParser(
                        request.META, request, request.upload_handlers, request.encoding
                    ).parse()
                    body_values = self.get_values(POST)
                    files_values = self.get_values(FILES)
                elif request.content_type == "application/x-www-form-urlencoded":
                    POST = QueryDict(request.body, encoding=request._encoding)
                    body_values = self.get_values(POST)
            # If there was a JSON body, go load that
            if request.content_type == "application/json" and request.body.strip():
                body_values.update(self.get_values(json.loads(request.body)))
            values = {}
            for name, sources in self.sources.items():
                for source in sources:
                    if source == InputSource.path:
                        if name in kwargs:
                            values[name] = kwargs[name]
                            break
                    elif source == InputSource.query:
                        if name in query_values:
                            values[name] = query_values[name]
                            break
                    elif source == InputSource.query_list:
                        if name in query_values:
                            values[name] = query_values[name]
                            if not isinstance(values[name], list):
                                values[name] = [values[name]]
                            break
                    elif source == InputSource.body:
                        if name in body_values:
                            values[name] = body_values[name]
                            break
                    elif source == InputSource.file:
                        if name in files_values:
                            values[name] = files_values[name]
                            break
                    elif source == InputSource.body_direct:
                        values[name] = body_values
                        break
                    elif source == InputSource.query_and_body_direct:
                        values[name] = dict(query_values)
                        values[name].update(body_values)
                        break
                    else:
                        raise ValueError(f"Unknown source {source}")
                else:
                    values[name] = None
            # Validate and coerce types
            try:
                model_instance = msgspec.convert(
                    values, type=self.input_model, strict=False
                )
            except msgspec.ValidationError as error:
                error_msg = str(error)
                error_details = [
                    {
                        "loc": ["<unknown>"],
                        "msg": error_msg,
                        "type": "value_error",
                    }
                ]
                return ApiResponse(
                    {"error": "invalid_input", "error_details": error_details},
                    status=400,
                    finalize=True,
                )
            view_kwargs = {
                name: getattr(model_instance, name)
                for name in model_instance.__struct_fields__
                if name in values and values[name] is not None  # Trim out missing fields
            }
            # Add in any files
            # TODO: HTTP error if file is not optional
            for name in self.input_files:
                view_kwargs[name] = files_values.get(name, None)
                
        try:
            response = self.view(request, **view_kwargs)
        except TypeError as error:
            # TODO: Handle this better by inspecting for default values on the view
            if "required positional argument" in str(error):
                return ApiResponse(
                    {"error": "invalid_input"},
                    status=400,
                    finalize=True,
                )
            raise
        except ApiError as error:
            return ApiResponse(
                {"error": error.error}, status=error.status, finalize=True
            )
        # If it's not an ApiResponse, make it one
        if not isinstance(response, ApiResponse):
            response = ApiResponse(response)
            
        if self.output_type is not None and self.validate_output:
            data_to_convert = convert_from_orm(response.data, self.output_type)
            validated = msgspec.convert(
                {"value": data_to_convert}, type=self.output_model, strict=False
            )
            response.data = msgspec.to_builtins(validated)["value"]
        elif isinstance(response.data, msgspec.Struct):
            response.data = msgspec.to_builtins(response.data)
        response.finalize()
        return response


api_view = ApiView
