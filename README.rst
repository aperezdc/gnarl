===================================================
 Lightweight Annotated Schema Serializable Objects
===================================================

.. image:: https://img.shields.io/travis/aperezdc/lasso-python.svg?style=flat
   :target: https://travis-ci.org/aperezdc/lasso-python
   :alt: Build Status

.. image:: https://img.shields.io/coveralls/aperezdc/lasso-python/master.svg?style=flat
   :target: https://coveralls.io/r/aperezdc/lasso-python?branch=master
   :alt: Code Coverage

.. |lasso-icon| image:: http://tango.freedesktop.org/static/cvs/tango-art-libre/22x22/tools/select-lasso.png

Lasso |lasso-icon| is a small module for `Python <http://python.org>`_ which
allows defining classes with type-checked attributes, conforming to a
predetermined schema.

Classes with Lasso |lasso-icon| schemas can be used to:

* **Type-check** object attributes.
* **Validate** input data.
* **Deserialize** input data to application objects, with direct support for
  deserializing `JSON <http://json.org>`_.
* **Serialize** application objects to JSON_.


Usage
=====

Define a class, with a schema attached to it used to type-check the
attributes:

   >>> from lasso import Schemed
   >>> class Point(Schemed):
   ...   __schema__ = { "x": int, "y": int }
   ...
   >>>

Now values can be created, using keyword arguments to set the values of the
attributes. Note how the attributes can be accessed normally:

   >>> location = Point(x=-3, y=5)
   >>> location.x, location.y
   (-3, 5)
   >>>

Attributes are type-checked:

   >>> location.x = 6  # Succeds
   >>> location.x = "invalid value"  # Fails
   Traceback (most recent call last):
      ...
   schema.SchemaError: 'invalid value' should be instance of <class 'int'>
   >>> location.x, location.y  # Values remain unchanged
   (6, 5)
   >>>

Last, but not least, conversion to and from JSON is automatically supported:

   >>> json_text = location.to_json(sort_keys=True)
   >>> json_text
   '{"x": 6, "y": 5}'
   >>> value = Point.from_json(json_text)
   >>> value.__class__.__name__
   'Point'
   >>>

