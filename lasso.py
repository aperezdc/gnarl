#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

"""
Lightweight schema-objects.
"""

from schema import Schema, SchemaError, And, Or, Use, Optional
from delorean import Delorean
import datetime
import uuid
import enum
import json


class LassoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "jsonable"):
            return o.jsonable
        else:
            return super(JSONEncoder, self).default(o)


class JSONable(object):
    def to_json(self, *arg, **kw):
        return json.dumps(self, cls=LassoJSONEncoder, *arg, **kw)

    @classmethod
    def from_json(cls, data, encoding=None):
        return cls.validate(json.loads(data))


class Enum(JSONable, enum.Enum):
    @classmethod
    def validate(cls, data):
        return cls(data)

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
    def validate(cls, data):
        from delorean.interface import parse
        d = parse(data)
        return cls(d.datetime, d.timezone)

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
    @classmethod
    def validate(cls, data):
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
        return object.__getattribute__(self, "_data").items()

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
