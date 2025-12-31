from typing import Any, get_args, get_origin

from .types import is_model_subclass

import msgspec
from django.db.models import Manager, QuerySet, Model
from django.db.models.fields.files import FieldFile
from django.template import Variable, VariableDoesNotExist


class Schema(msgspec.Struct, omit_defaults=True, gc=False):
    """Base schema class with Django ORM support."""

    @classmethod
    def from_orm(cls, obj: Any):
        """Convert a Django ORM object to a schema instance."""
        data = {}
        for field_name in cls.__struct_fields__:
            try:
                value = getattr(obj, field_name)
            except AttributeError:
                try:
                    value = Variable(field_name).resolve(obj)
                except VariableDoesNotExist:
                    continue

            if isinstance(value, Manager):
                value = list(value.all())
            elif isinstance(value, getattr(QuerySet, "__origin__", QuerySet)):
                value = list(value)
            elif callable(value):
                value = value()
            elif isinstance(value, FieldFile):
                value = value.url if value else None

            data[field_name] = value

        return msgspec.convert(data, type=cls)

    def dict(self) -> dict[str, Any]:
        """Convert schema instance to a dictionary."""
        return msgspec.to_builtins(self)


def convert_from_orm(data: Any, target_type: Any) -> Any:
    """
    Convert Django ORM data to Schema instances based on target type.
    """
    if not target_type:
        return data

    origin = get_origin(target_type)

    # Handle collections: list[Schema], set[Schema], tuple[Schema]
    if origin in (list, set, tuple) and data:
        first_item = next(iter(data), None)
        if first_item and isinstance(first_item, Model):
            schema_type = get_args(target_type)[0]
            if is_model_subclass(schema_type):
                converted = [schema_type.from_orm(obj) for obj in data]
                # Preserve collection type (list vs set vs tuple)
                return origin(converted) if origin else converted

    # Handle single object: Schema
    elif isinstance(data, Model) and is_model_subclass(target_type):
        return target_type.from_orm(data)

    return data
