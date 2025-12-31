from typing import Any, Dict

import msgspec
from django.db.models import Manager, QuerySet
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

    def dict(self) -> Dict[str, Any]:
        """Convert schema instance to a dictionary."""
        return msgspec.to_builtins(self)
