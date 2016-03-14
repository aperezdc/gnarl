#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

"""
Lightweight Annotated Schema Serializable Objects.
"""

from schema import Schema, SchemaError, And, Or, Use, Optional
from delorean import Delorean
import uuid
import enum
import json


class LassoJSONEncoder(json.JSONEncoder):
    """
    JSON encoder that can encode arbitrary types.

    To make any type (class) serializable, it is enough that it provides a
    `jsonable` attribute which returns a primitive value that the JSON encoder
    from the Python standard library (`json.JSONEncoder`) can understand.

    For example, the following defins a ``Timestamp`` class that wraps a
    `datetime.datetime` object to make it serializable:

    .. code-block:: python

        class Timestamp(object):
            def __init__(self, dt):
                self.datetime = dt

            @property
            def jsonable(self):
                # Return a 'str'value
                return self.datetime.isoformat()
    """
    def default(self, o):
        if hasattr(o, "jsonable"):
            return o.jsonable
        else:  # pragma: nocover
            return super(JSONEncoder, self).default(o)


class JSONable(object):
    """
    Mix-in class which adds methods to serialize to/from JSON.
    """
    def to_json(self, *arg, **kw):
        """
        Serializes an object to JSON using `LassoJSONEncoder`.

        Positional and keyword arguments are passed down to the `json.dump()`
        function from the Python standard library.
        """
        return json.dumps(self, cls=LassoJSONEncoder, *arg, **kw)

    @classmethod
    def from_json(cls, data, encoding=None):
        """
        Deserializes an object from JSON and validates it.

        Loads data from a JSON string, decoding it with the `json.loads()`
        function from the Python standard library, and the resulting value
        is passed to a `.validate()` class method. This method is responsible
        to validate the input data, and optionally return an object which
        represents the deserialized data.
        """
        return cls.validate(json.loads(data))


class Enum(JSONable, enum.Enum):
    """
    Provides support for enumeration values as Lasso schema objects.

    The `Enum` class augments the standard `enum.Enum`, providing support to
    use it as a schema type:

    .. code-block:: python

        class Tristate(lasso.Enum):
            TRUE      = "#t"
            FALSE     = "#f"
            UNDEFINED = "#nil"

        class Checkbox(lasso.Schemed):
            __schema__ = { "state": Tristate, "label": str }
    """
    @classmethod
    def validate(cls, data):
        return data if isinstance(data, cls) else cls(data)

    @property
    def jsonable(self):
        return self.value


class Timestamp(Delorean, JSONable):
    FORMAT_ISO_8601      = object()
    FORMAT_RFC_2822      = "%a, %d %b %Y %H:%M:%S %z"
    FORMAT_RFC_8601_DATE = "%Y-%d-%m"
    FORMAT_RFC_2822_DATE = "%a, %d %b %Y"

    __format__ = FORMAT_ISO_8601

    def __str__(self):
        if self.__format__ is self.FORMAT_ISO_8601:
            return self.datetime.isoformat()
        else:
            return self.datetime.strftime(self.__format__)

    jsonable = property(__str__)

    @classmethod
    def validate(cls, data, timezone=None):
        from datetime import datetime

        if isinstance(data, cls):
            return data
        elif isinstance(data, datetime):
            if timezone is None:
                timezone = "UTC"
            return cls(data, timezone)
        else:
            if not isinstance(data, Delorean):
                from delorean.interface import parse
                data = parse(data)
            return cls(data.datetime, data.timezone)

    @classmethod
    def now(cls):
        from delorean.interface import now
        d = now()
        d.truncate("second")
        return cls(d.datetime, d.timezone)

    utcnow = now

    @classmethod
    def today(cls):
        from delorean.interface import now
        d = now()
        d.truncate("day")
        return cls(d.datetime, d.timezone)


class UUID(uuid.UUID, JSONable):
    X500 = uuid.NAMESPACE_X500
    URL  = uuid.NAMESPACE_URL
    DNS  = uuid.NAMESPACE_DNS
    OID  = uuid.NAMESPACE_OID

    @classmethod
    def validate(cls, data):
        if isinstance(data, cls):
            return data
        elif isinstance(data, uuid.UUID):
            return cls(str(data))
        else:
            return cls(data)

    @property
    def jsonable(self):
        return str(self)

    @classmethod
    def uuid1(cls, *arg, **kw):
        return cls(str(uuid.uuid1(*arg, **kw)))

    @classmethod
    def uuid3(cls, *arg, **kw):
        return cls(str(uuid.uuid3(*arg, **kw)))

    @classmethod
    def uuid4(cls, *arg, **kw):
        return cls(str(uuid.uuid4(*arg, **kw)))

    @classmethod
    def uuid5(cls, *arg, **kw):
        return cls(str(uuid.uuid5(*arg, **kw)))


class _SchemedMeta(type):
    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, classdict)
        if not isinstance(result.__schema__, Schema):
            result.__schema__ = Schema(result.__schema__)
        return result


class Schemed(JSONable, metaclass=_SchemedMeta):
    __schema__ = None
    __slots__  = ("_data",)

    def __init__(self, *arg, **kw):
        object.__setattr__(self, "_data", ())
        self.update(*arg, **kw)

    def __getattr__(self, key):
        d = object.__getattribute__(self, "_data")
        if key in d:
            return d[key]
        else:
            return object.__getattribute__(self, key)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self.update({ key: value })

    def update(self, *arg, **kw):
        d = dict(object.__getattribute__(self, "_data"))
        d.update(*arg, **kw)
        object.__setattr__(self, "_data", self.__schema__.validate(d))
        return self

    @property
    def jsonable(self):
        return object.__getattribute__(self, "_data")

    def __iter__(self):
        return ((k, v) for (k, v)
                in object.__getattribute__(self, "_data").items())

    def keys(self):
        return self._data.keys()

    @classmethod
    def validate(cls, data):
        if isinstance(data, cls):
            return data
        elif isinstance(data, dict):
            return cls(**data)
        else:
            raise ValueError(data)
