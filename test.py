#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the MIT license.

import unittest
from lasso import Enum, Schemed, Schema, SchemaError, Optional, UUID, Timestamp


class Continent(Enum):
    EUROPE     = "EUROPE"
    ASIA       = "ASIA"
    AMERICA    = "AMERICA"
    OCEANIA    = "OCEANIA"
    ANTARCTICA = "ANTARCTICA"

class WithContinent(Schemed):
    __schema__ = Schema({
        "continent" : Continent,
    })

    def __eq__(self, other):
        return self.continent == other.continent


class TestEnum(unittest.TestCase):
    def test_validate(self):
        """
        Check whether .validate() can be used as a class method and that it
        produces a meaningful value.
        """
        value = Continent.validate("EUROPE")
        self.assertEqual(Continent.EUROPE, value)

    def test_validate_object(self):
        """
        Check whether .validate() transparently accepts instances of the Enum
        as parameters, and returns themselves unmodified.
        """
        data = Continent.EUROPE
        value = Continent.validate(data)
        self.assertEqual(Continent.EUROPE, value)
        self.assertIs(value, data)
        self.assertEqual(value, data)

    def test_to_json_with_continent(self):
        """
        Check whether serialization of an Enum value produces the expected
        JSON output.
        """
        value = WithContinent(continent=Continent.EUROPE)
        self.assertEqual('{"continent": "EUROPE"}', value.to_json())

    def test_to_json(self):
        """
        Check whether an enum can be properly serialized.
        """
        self.assertEqual('"EUROPE"', Continent.EUROPE.to_json())

    def test_json_roundtrip(self):
        """
        Check wether an object with enums serializes properly to JSON and can
        be deserialized back.
        """
        value = WithContinent(continent=Continent.EUROPE)
        json = value.to_json()
        self.assertEqual(value, WithContinent.from_json(json))


class TestUUID(unittest.TestCase):
    valid = (
        "5c2ddc84-bf99-47d2-a0da-3882b9d788ed",
        "5C2DDC84-BF99-47D2-A0DA-3882B9D788ED",
        "5c2ddc84bf9947d2a0da3882b9d788ed",
        "5C2DDC84BF9947D2A0DA3882B9D788ED",
    )
    invalid = (
        "",
        "blargh",
        "AFCEDEFSDSDS",
    )

    def test_parse_valid_uuids(self):
        for u in self.valid:
            uuid = UUID.validate(u)
            self.assertIsInstance(uuid, UUID)

    def test_parse_invalid_uuids(self):
        for u in self.invalid:
            with self.assertRaises(ValueError):
                r = UUID.validate(u)

    def test_json_roundtrip(self):
        from uuid import uuid4
        value = UUID.uuid4()
        self.assertEqual(value, UUID.from_json(value.to_json()))

    def test_validate_object(self):
        data = UUID.uuid4()
        value = UUID.validate(data)
        self.assertIsInstance(value, UUID)
        self.assertIs(value, data)

    def test_validate_uuid_stdlib_object(self):
        import uuid
        data = uuid.uuid4()
        value = UUID.validate(data)
        self.assertIsInstance(value, UUID)
        self.assertEqual(data, value)

    def test_instantiate_uuid1(self):
        import uuid
        value = UUID.uuid1()
        self.assertIsInstance(value, UUID)
        self.assertIsInstance(value, uuid.UUID)

    def test_instantiate_uuid3(self):
        import uuid
        value = UUID.uuid3(UUID.URL, "http://lasso.org")
        self.assertIsInstance(value, UUID)
        self.assertIsInstance(value, uuid.UUID)

    def test_instantiate_uuid4(self):
        import uuid
        value = UUID.uuid4()
        self.assertIsInstance(value, UUID)
        self.assertIsInstance(value, uuid.UUID)

    def test_instantiate_uuid5(self):
        import uuid
        value = UUID.uuid5(UUID.URL, "http://lasso.org")
        self.assertIsInstance(value, UUID)
        self.assertIsInstance(value, uuid.UUID)


class RFC2822Timestamp(Timestamp):
    __format__ = Timestamp.FORMAT_RFC_2822

class RFC2822Date(Timestamp):
    __formt__ = Timestamp.FORMAT_RFC_2822_DATE


class TestTimestamp(unittest.TestCase):
    valid = (
        "Mon, 22 Jun 2015",
        "Thu, 11 May 1983",
        "Mon, 22 Jun 2015 22:26:00 +0100",
        "Thu, 11 May 1983 19:35:45 -0230",
        "1983-05-11T19:35:45+0100",
        "1983-05-11 19:35:45 +01:00",
    )

    invalid = (
        "Blargh",
        "123456768232342342",
        # XXX: This is invalid because the date does not fall on Tuesday.
        #      In most systems strptime() does not check the given week day.
        # "Tue, 22 Jun 2015 22:26:00 +0100",
    )

    def test_parse_valid_timestamps(self):
        for date in self.valid:
            d = RFC2822Timestamp.validate(date)
            self.assertIsInstance(d, Timestamp)
            self.assertIsInstance(d, RFC2822Timestamp)
            d = RFC2822Date.validate(date)
            self.assertIsInstance(d, Timestamp)
            self.assertIsInstance(d, RFC2822Date)

    def test_parse_invalid_dates(self):
        for date in self.invalid:
            with self.assertRaises(ValueError):
                d = RFC2822Timestamp.validate(date)
            with self.assertRaises(ValueError):
                d = RFC2822Date.validate(date)

    def test_json_roundtrip_rfc2822timestamp(self):
        now = RFC2822Timestamp.now()
        self.assertIsInstance(now, RFC2822Timestamp)
        self.assertEqual(now, RFC2822Timestamp.from_json(now.to_json()))

    def test_json_roundtrip_rfc2822date(self):
        now = RFC2822Date.today()
        self.assertIsInstance(now, RFC2822Date)
        self.assertEqual(now, RFC2822Date.from_json(now.to_json()))

    def test_validate_object(self):
        data = Timestamp.now()
        now = Timestamp.validate(data)
        self.assertIs(now, data)
        self.assertEqual(now, data)

    def test_validate_datetime_object(self):
        from datetime import datetime
        data = datetime.utcnow()
        now = Timestamp.validate(data)
        self.assertIsInstance(now, Timestamp)
        dnow = Timestamp(data, "UTC")
        self.assertEqual(now, dnow)

    def test_validate_delorean_object(self):
        from delorean import Delorean
        data = Delorean()
        now = Timestamp.validate(data)
        self.assertIsInstance(now, Timestamp)
        self.assertEqual(data, now)


class TestSchemaShape(unittest.TestCase):
    def test_schema_automatic_creation(self):
        """
        Checks whether the __schema__ class attribute is automatically turned
        into a Schema instance.
        """
        class Point(Schemed):
            __schema__ = { "x": float, "y": float }
        self.assertIsInstance(Point.__schema__, Schema)

    def test_schema_manual_creation(self):
        """
        Checks that creating the __schema__ class attribute directly using the
        Schema constructor works as expected.
        """
        class Point(Schemed):
            __schema__ = Schema({ "x": float, "y": float })
        self.assertIsInstance(Point.__schema__, Schema)

    def test_instance_fields(self):
        """
        Checks that fields defined in the schema are available in instances.
        """
        class Point(Schemed):
            __schema__ = { "x": float, "y": float }

        origin = Point(x=0.0, y=0.0)
        self.assertTrue(hasattr(origin, "x"))
        self.assertTrue(hasattr(origin, "y"))

    def test_optional_instance_fields(self):
        """
        Checks whether schema fields marked with Optional() are indeed
        optional, and the attributes only reported as present when the
        instances are created with the attributes defined.
        """
        class Point(Schemed):
            __schema__ = { "x": float, "y": float, Optional("z"): float }

        origin_2d = Point(x=0.0, y=0.0)
        self.assertFalse(hasattr(origin_2d, "z"))

        origin_3d = Point(x=0.0, y=0.0, z=0.0)
        self.assertTrue(hasattr(origin_3d, "z"))

    def test_instantiate_wrong_value_type(self):
        class Point(Schemed):
            __schema__ = { "x": float, "y": float }
        with self.assertRaises(SchemaError):
            origin = Point(x=0, y=0.0)

    def test_instantiate_missing_field(self):
        class Point(Schemed):
            __schema__ = { "x": float, "y": float }
        with self.assertRaises(SchemaError):
            origin = Point(x=0.0)

    def test_instantiate_extra_field(self):
        class Point(Schemed):
            __schema__ = { "x": float, "y": float }
        with self.assertRaises(SchemaError):
            origin = Point(x=0.0, y=0.0, z="OUCH")


class ListValue(Schemed):
    __schema__ = { "value": [int] }
class DictValue(Schemed):
    __schema__ = { "value": { Optional("n"): int } }
class NestedValue(Schemed):
    __schema__ = { "value": ListValue }

class TestToJSON(unittest.TestCase):
    def test_empty_list(self):
        lv = ListValue(value=[])
        self.assertIsInstance(lv.value, list)
        self.assertEqual('{"value": []}', lv.to_json())

    def test_list(self):
        lv = ListValue(value=[1, 2, 3])
        self.assertEqual('{"value": [1, 2, 3]}', lv.to_json())

    def test_empty_dict(self):
        dv = DictValue(value={})
        self.assertEqual('{"value": {}}', dv.to_json())

    def test_dict(self):
        dv = DictValue(value={"n": 42})
        self.assertEqual('{"value": {"n": 42}}', dv.to_json())

    def test_nested(self):
        nv = NestedValue(value=ListValue(value=[1, 2, 3]))
        self.assertEqual('{"value": {"value": [1, 2, 3]}}', nv.to_json())


class TestFromJSON(unittest.TestCase):
    def test_empty_list(self):
        lv = ListValue.from_json('{"value": []}')
        self.assertListEqual([], lv.value)

    def test_list(self):
        lv = ListValue.from_json('{"value": [1, 2, 3]}')
        self.assertListEqual([1, 2, 3], lv.value)

    def test_empty_dict(self):
        dv = DictValue.from_json('{"value":{}}')
        self.assertDictEqual({}, dv.value)

    def test_dict(self):
        dv = DictValue.from_json('{"value": {"n": 121}}')
        self.assertDictEqual({"n": 121}, dv.value)

    def test_nested(self):
        nv = NestedValue.from_json('{"value": {"value": [4, 5, 6]}}')
        self.assertIsInstance(nv.value, ListValue)
        self.assertListEqual([4, 5, 6], nv.value.value)
