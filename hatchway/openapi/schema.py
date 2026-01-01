"""
OpenAPI schema generation from msgspec.Struct models and Python type annotations.
"""

from __future__ import annotations

import typing
from datetime import date, datetime
from typing import Any, get_args, get_origin

import msgspec
import msgspec.inspect


def msgspec_type_to_openapi(msgspec_type) -> dict[str, Any]:
    """
    Convert a msgspec.inspect type to an OpenAPI schema.

    Args:
        msgspec_type: A msgspec type descriptor (IntType, StrType, etc.)

    Returns:
        OpenAPI schema dictionary
    """
    # Handle basic types
    if isinstance(msgspec_type, msgspec.inspect.IntType):
        schema = {"type": "integer"}
        if msgspec_type.gt is not None:
            schema["minimum"] = msgspec_type.gt
            schema["exclusiveMinimum"] = True
        elif msgspec_type.ge is not None:
            schema["minimum"] = msgspec_type.ge
        if msgspec_type.lt is not None:
            schema["maximum"] = msgspec_type.lt
            schema["exclusiveMaximum"] = True
        elif msgspec_type.le is not None:
            schema["maximum"] = msgspec_type.le
        if msgspec_type.multiple_of is not None:
            schema["multipleOf"] = msgspec_type.multiple_of
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.FloatType):
        schema = {"type": "number", "format": "double"}
        if msgspec_type.gt is not None:
            schema["minimum"] = msgspec_type.gt
            schema["exclusiveMinimum"] = True
        elif msgspec_type.ge is not None:
            schema["minimum"] = msgspec_type.ge
        if msgspec_type.lt is not None:
            schema["maximum"] = msgspec_type.lt
            schema["exclusiveMaximum"] = True
        elif msgspec_type.le is not None:
            schema["maximum"] = msgspec_type.le
        if msgspec_type.multiple_of is not None:
            schema["multipleOf"] = msgspec_type.multiple_of
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.StrType):
        schema = {"type": "string"}
        if msgspec_type.min_length is not None:
            schema["minLength"] = msgspec_type.min_length
        if msgspec_type.max_length is not None:
            schema["maxLength"] = msgspec_type.max_length
        if msgspec_type.pattern is not None:
            schema["pattern"] = msgspec_type.pattern
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.BoolType):
        return {"type": "boolean"}

    elif isinstance(msgspec_type, msgspec.inspect.BytesType):
        schema = {"type": "string", "format": "binary"}
        if msgspec_type.min_length is not None:
            schema["minLength"] = msgspec_type.min_length
        if msgspec_type.max_length is not None:
            schema["maxLength"] = msgspec_type.max_length
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.DateTimeType):
        return {"type": "string", "format": "date-time"}

    elif isinstance(msgspec_type, msgspec.inspect.DateType):
        return {"type": "string", "format": "date"}

    elif isinstance(msgspec_type, msgspec.inspect.NoneType):
        return {"type": "null"}

    elif isinstance(msgspec_type, msgspec.inspect.ListType):
        item_schema = msgspec_type_to_openapi(msgspec_type.item_type)
        schema = {"type": "array", "items": item_schema}
        if msgspec_type.min_length is not None:
            schema["minItems"] = msgspec_type.min_length
        if msgspec_type.max_length is not None:
            schema["maxItems"] = msgspec_type.max_length
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.SetType):
        item_schema = msgspec_type_to_openapi(msgspec_type.item_type)
        schema = {"type": "array", "items": item_schema, "uniqueItems": True}
        if msgspec_type.min_length is not None:
            schema["minItems"] = msgspec_type.min_length
        if msgspec_type.max_length is not None:
            schema["maxItems"] = msgspec_type.max_length
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.DictType):
        value_schema = msgspec_type_to_openapi(msgspec_type.value_type)
        schema = {"type": "object", "additionalProperties": value_schema}
        if msgspec_type.min_length is not None:
            schema["minProperties"] = msgspec_type.min_length
        if msgspec_type.max_length is not None:
            schema["maxProperties"] = msgspec_type.max_length
        return schema

    elif isinstance(msgspec_type, msgspec.inspect.UnionType):
        types = [msgspec_type_to_openapi(t) for t in msgspec_type.types]
        # Check if this is an optional (union with None)
        non_null_types = [t for t in types if t.get("type") != "null"]
        if len(types) != len(non_null_types):
            # This is optional
            if len(non_null_types) == 1:
                schema = non_null_types[0].copy()
                schema["nullable"] = True
                return schema
            else:
                return {"oneOf": non_null_types, "nullable": True}
        else:
            return {"oneOf": types}

    elif isinstance(msgspec_type, msgspec.inspect.StructType):
        return {"$ref": f"#/components/schemas/{msgspec_type.cls.__name__}"}

    # Fallback
    return {"type": "string"}


def get_openapi_type(python_type: Any) -> dict[str, Any]:
    """
    Convert a Python type annotation to OpenAPI schema type.

    Args:
        python_type: The Python type to convert

    Returns:
        OpenAPI schema dictionary
    """
    # Handle None type
    if python_type is type(None):
        return {"type": "null"}

    # Get the origin for generic types (list, dict, etc.)
    origin = get_origin(python_type)

    # Handle Optional types (Union with None)
    if origin is typing.Union:
        args = get_args(python_type)
        # Check if this is Optional (has None in the union)
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(args) != len(non_none_args):
            # This is Optional[T]
            if len(non_none_args) == 1:
                schema = get_openapi_type(non_none_args[0])
                schema["nullable"] = True
                return schema
            else:
                # Union of multiple types with None
                return {
                    "oneOf": [get_openapi_type(arg) for arg in non_none_args],
                    "nullable": True,
                }
        else:
            # Union without None
            return {"oneOf": [get_openapi_type(arg) for arg in args]}

    # Handle list types
    if origin is list:
        args = get_args(python_type)
        if args:
            return {"type": "array", "items": get_openapi_type(args[0])}
        return {"type": "array", "items": {}}

    # Handle set types (same as list in OpenAPI)
    if origin is set:
        args = get_args(python_type)
        if args:
            return {
                "type": "array",
                "items": get_openapi_type(args[0]),
                "uniqueItems": True,
            }
        return {"type": "array", "items": {}, "uniqueItems": True}

    # Handle dict types
    if origin is dict:
        args = get_args(python_type)
        if len(args) >= 2:
            return {
                "type": "object",
                "additionalProperties": get_openapi_type(args[1]),
            }
        return {"type": "object", "additionalProperties": True}

    # Handle basic Python types
    type_mapping = {
        int: {"type": "integer"},
        float: {"type": "number", "format": "double"},
        str: {"type": "string"},
        bool: {"type": "boolean"},
        bytes: {"type": "string", "format": "binary"},
        datetime: {"type": "string", "format": "date-time"},
        date: {"type": "string", "format": "date"},
    }

    if python_type in type_mapping:
        return type_mapping[python_type]

    # Handle msgspec.Struct subclasses
    if isinstance(python_type, type) and issubclass(python_type, msgspec.Struct):
        return {"$ref": f"#/components/schemas/{python_type.__name__}"}

    # Fallback for unknown types
    return {"type": "string"}


def get_msgspec_constraints(field_info: msgspec.inspect.FieldInfo) -> dict[str, Any]:
    """
    Extract validation constraints from msgspec field metadata.

    Args:
        field_info: msgspec field information

    Returns:
        Dictionary of OpenAPI validation keywords
    """
    constraints = {}

    # Check for msgspec.Meta constraints
    if hasattr(field_info, "encode_name"):
        # This field might have metadata
        pass

    # Note: msgspec uses typing.Annotated for constraints
    # We'll need to extract these from the type annotation
    return constraints


def struct_to_schema(struct_class: type[msgspec.Struct]) -> dict[str, Any]:
    """
    Convert a msgspec.Struct class to an OpenAPI schema.

    Args:
        struct_class: The msgspec.Struct subclass

    Returns:
        OpenAPI schema dictionary
    """
    if not (isinstance(struct_class, type) and issubclass(struct_class, msgspec.Struct)):
        raise ValueError(f"{struct_class} is not a msgspec.Struct subclass")

    # Get struct fields
    struct_info = msgspec.inspect.type_info(struct_class)

    if not isinstance(struct_info, msgspec.inspect.StructType):
        raise ValueError(f"{struct_class} is not a Struct type")

    properties = {}
    required = []

    for field in struct_info.fields:
        # Use msgspec_type_to_openapi for msgspec type descriptors
        field_schema = msgspec_type_to_openapi(field.type)

        # Add constraints from metadata
        constraints = get_msgspec_constraints(field)
        field_schema.update(constraints)

        properties[field.encode_name] = field_schema

        # Check if field is required (no default value)
        if field.required:
            required.append(field.encode_name)

    schema = {
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    # Add description from docstring if available
    if struct_class.__doc__:
        schema["description"] = struct_class.__doc__.strip()

    return schema


def collect_schema_definitions(
    python_type: Any, definitions: dict[str, dict[str, Any]] | None = None
) -> dict[str, dict[str, Any]]:
    """
    Recursively collect all msgspec.Struct schema definitions from a type.

    Args:
        python_type: The Python type or msgspec type to scan
        definitions: Dictionary to collect definitions (updated in-place)

    Returns:
        Dictionary of schema name -> schema definition
    """
    if definitions is None:
        definitions = {}

    # Handle msgspec inspect types
    if isinstance(python_type, msgspec.inspect.UnionType):
        for type_item in python_type.types:
            collect_schema_definitions(type_item, definitions)
        return definitions

    elif isinstance(python_type, (msgspec.inspect.ListType, msgspec.inspect.SetType)):
        collect_schema_definitions(python_type.item_type, definitions)
        return definitions

    elif isinstance(python_type, msgspec.inspect.DictType):
        collect_schema_definitions(python_type.value_type, definitions)
        return definitions

    elif isinstance(python_type, msgspec.inspect.StructType):
        schema_name = python_type.cls.__name__
        if schema_name not in definitions:
            # Add the schema
            definitions[schema_name] = struct_to_schema(python_type.cls)

            # Recursively scan fields for nested structs
            for field in python_type.fields:
                collect_schema_definitions(field.type, definitions)
        return definitions

    # Handle regular Python types
    # Get the origin for generic types
    origin = get_origin(python_type)

    # Handle Union types
    if origin is typing.Union:
        for arg in get_args(python_type):
            collect_schema_definitions(arg, definitions)
        return definitions

    # Handle list/set types
    if origin in (list, set):
        args = get_args(python_type)
        if args:
            collect_schema_definitions(args[0], definitions)
        return definitions

    # Handle dict types
    if origin is dict:
        args = get_args(python_type)
        if len(args) >= 2:
            collect_schema_definitions(args[1], definitions)
        return definitions

    # Handle msgspec.Struct subclasses
    if isinstance(python_type, type) and issubclass(python_type, msgspec.Struct):
        schema_name = python_type.__name__
        if schema_name not in definitions:
            # Add the schema
            definitions[schema_name] = struct_to_schema(python_type)

            # Recursively scan fields for nested structs
            struct_info = msgspec.inspect.type_info(python_type)
            if isinstance(struct_info, msgspec.inspect.StructType):
                for field in struct_info.fields:
                    collect_schema_definitions(field.type, definitions)

    return definitions
