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

from collections import namedtuple
from delorean import Delorean
import uuid
import enum
import json


def _get_callable_repr(c):
    return c.__name__ if hasattr(c, "__name__") else repr(c)


class SchemaError(Exception):
    """
    Error occured during schema validation.
    """
    @property
    def message(self):
        """Error message."""
        return self.args[0]


_OPTIONAL_NO_DEFAULT_MARK = object()
class Optional(namedtuple("_Optional", "schema,default")):
    """
    Marks an element in a dictionary schema as optional.

    For example, the following creates a schema which validates a dictionary,
    where the ``name`` key is optional, and the ``

    .. code-block:: python

        Schema({
            "login": str,
            "name": Optional(str),
            "age": Optional(int, default=0),
        })
    """
    __slots__ = ()

    def __new__(cls, schema, default=_OPTIONAL_NO_DEFAULT_MARK):
        return super(Optional, cls).__new__(cls, schema, default)


class And(namedtuple("_And", "args,error")):
    __slots__ = ()

    def __new__(cls, *args, error=None):
        return super(And, cls).__new__(cls, args, error)

    def __repr__(self):
        return "{!s}({!s})".format(self.__class__.__name__,
                ", ".join(repr(a) for a in self.args))

    def validate(self, data):
        for s in (Schema(s, self.error) for s in self.args):
            data = s.validate(data)
        return data


class Or(And):
    __slots__ = ()

    def validate(self, data):
        for s in (Schema(s, self.error) for s in self.args):
            try:
                return s.validate(data)
            except SchemaError as ex:
                pass
        raise SchemaError(self.error if self.error is not None
                else "{!r} did not validate {!r}".format(data, self))


class Use(namedtuple("_Use", "func,error")):
    __slots__ = ()

    def __new__(cls, func, error=None):
        assert callable(func)
        return super(Use, cls).__new__(cls, func, error)

    def __repr__(self):
        return "{!s}({!r})".format(self.__class__.__name__, self.func)

    def validate(self, data):
        try:
            return self.func(data)
        except SchemaError as ex:
            raise ex if self.error is None else SchemaError(self.error)
        except BaseException as ex:
            f = _get_callable_repr(self.func)
            raise SchemaError(self.error if self.error is not None
                    else "{!s}({!r}) raised {!r}".format(f, data, ex))


class StringMatch(namedtuple("_StringMatch", "regex,error")):
    __slots__ = ()

    def __new__(cls, pattern, error=None, *arg, **kw):
        from re import compile as re_compile
        return super(StringMatch, cls).__new__(cls, re_compile(pattern, *arg, **kw), error)

    def __repr__(self):
        return "{!s}({!r})".format(self.__class__.__name__, self.regex.pattern)

    def validate(self, data):
        if isinstance(data, str):
            if self.regex.match(data):
                return data
            raise SchemaError(self.error if self.error is not None else
                    "{!r} does not match regex {!r}".format(data, self.regex.pattern))
        else:
            raise SchemaError(self.error if self.error is not None else
                    "{!r} is not a string".format(data))


class Schema(object):
    __slots__ = ("_schema", "_error")

    def __init__(self, schema, error=None):
        self._schema = schema
        self._error = error

    def __repr__(self):
        return "{!s}({!r})".format(self.__class__.__name__, self._schema)

    def __pcall(self, f, data, exc_format=None, *exc_args):
        try:
            return f(data)
        except SchemaError as ex:
            raise ex if self._error is None else SchemaError(self._error)
        except BaseException as ex:
            e = self._error
            if e is None:
                if exc_format is None:
                    e = "{!s}({!r})".format(f, data)
                else:
                    e = exc_format.format(*exc_args)
                e += " raised {!r}".format(ex)
            raise SchemaError(e)

    def validate(self, data):
        s = self._schema
        e = self._error
        if callable(getattr(s, "validate", None)):
            return self.__pcall(s.validate, data, "{!r}.validate({!r})", s, data)
        if isinstance(s, (list, tuple, set, frozenset)):
            data = Schema(type(s), e).validate(data)
            o = Or(*s, error=e)
            return type(data)(o.validate(d) for d in data)
        if isinstance(s, dict):
            data = Schema(dict, e).validate(data)
            new = type(data)()
            seen = set()
            for k, v in s.items():
                if type(v) is Optional:
                    if k in data:
                        new[k] = Schema(v.schema, e).validate(data[k])
                        seen.add(k)
                elif k in data:
                    new[k] = Schema(v, e).validate(data[k])
                    seen.add(k)
            required = set(k for k, v in s.items() if type(v) is not Optional)
            if not required.issubset(seen):
                missing = ", ".join(repr(k) for k in sorted(required - seen))
                raise SchemaError("Missing keys: " + missing)
            extra = data.keys() - s.keys()
            if len(extra):
                extra = ", ".join(repr(k) for k in sorted(extra))
                raise SchemaError("Wrong keys in {!r}: {!s}".format(data, extra))
            # Apply optionals with default values
            defaults = set(k for k, v in s.items() if type(v) is Optional
                    and v.default is not _OPTIONAL_NO_DEFAULT_MARK) - seen
            for k in defaults:
                new[k] = s[k].default
            return new
        if issubclass(type(s), type):
            if isinstance(data, s):
                return data
            else:
                raise SchemaError(e if e is not None else
                        "{!r} should be instance of {!r}".format(data, s))
        if callable(s):
            if self.__pcall(s, data):
                return data
            raise SchemaError(e if e is not None
                    else "{!s}({!r}) should evaluate to True".format(
                        _get_callable_repr(s), data))
        if s == data:
            return data
        else:
            raise SchemaError(e if e is not None else
                    "{!r} should be {!r}".format(data, s))


class GnarlJSONEncoder(json.JSONEncoder):
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
        Serializes an object to JSON using `GnarlJSONEncoder`.

        Positional and keyword arguments are passed down to the `json.dump()`
        function from the Python standard library.
        """
        return json.dumps(self, cls=GnarlJSONEncoder, *arg, **kw)

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

    @staticmethod
    def __to_hipack_serializable(o):
        return (o.jsonable if hasattr(o, "jsonable") else o, None)

    def to_hipack(self, indent=False):
        """
        Serializes an object to HiPack.

        The `indent` argument is passed to `hipack.dumps()`.
        """
        from hipack import dumps
        return dumps(self, indent=indent, value=self.__to_hipack_serializable)

    @classmethod
    def from_hipack(cls, data, encoding=None):
        """
        Deserializes an object from HiPack and validates it.

        Loads data from a HiPack string, decoding it with `hipack.loads()`,
        and the resulting value is passed to a `.validate()` class method.
        That method is responsible of validating the input date, and
        optionally returning an object which represents the deserialized
        data.
        """
        from hipack import loads
        return cls.validate(loads(data))


class Enum(JSONable, enum.Enum):
    """
    Provides support for enumeration values as Gnarl schema objects.

    The `Enum` class augments the standard `enum.Enum`, providing support to
    use it as a schema type:

    .. code-block:: python

        class Tristate(gnarl.Enum):
            TRUE      = "#t"
            FALSE     = "#f"
            UNDEFINED = "#nil"

        class Checkbox(gnarl.Schemed):
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
                data = parse(data, dayfirst=False)
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
