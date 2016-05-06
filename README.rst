===================================================
 Lightweight Annotated Schema Serializable Objects
===================================================

.. image:: https://readthedocs.org/projects/gnarl/badge/?version=latest
   :target: https://gnarl.readthedocs.io/en/latest
   :alt: Documentation Status

.. image:: https://img.shields.io/travis/aperezdc/gnarl.svg?style=flat
   :target: https://travis-ci.org/aperezdc/gnarl
   :alt: Build Status

.. image:: https://img.shields.io/coveralls/aperezdc/gnarl/master.svg?style=flat
   :target: https://coveralls.io/r/aperezdc/gnarl?branch=master
   :alt: Code Coverage

.. |knot-icon| image:: https://github.com/aperezdc/gnarl/raw/master/doc/knot.png

Gnarl |knot-icon| is a small module for `Python <http://python.org>`_ which
allows defining classes with type-checked attributes, conforming to a
predetermined schema.

Classes with Gnarl |knot-icon| schemas can be used to:

* **Type-check** object attributes.
* **Validate** input data.
* **Deserialize** input data to application objects, with direct support for
  deserializing `JSON <http://json.org>`_.
* **Serialize** application objects to JSON_.


Usage
=====

Define a class, with a schema attached to it used to type-check the
attributes:

   >>> from gnarl import Schemed
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
   gnarl.SchemaError: 'invalid value' should be instance of <class 'int'>
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


Installation
============

The stable releases are uploaded to `PyPI <https://pypi.python.org>`_, so you
can install them and upgrade using ``pip``::

   pip install gnarl

Alternatively, you can install development versions —at your own risk—
directly from the Git repository::

   pip install -e git://github.com/aperezdc/gnarl


Documentation
=============

The documentation for Gnarl |knot-icon| is available at:

  http://gnarl.readthedocs.io/en/latest

Note that the documentation is work in progress. In the meanwhile, you may
want to read the source code of the module itself for additional insight,
or even better, the code of `projects using the module`__.

__ users_


Development
===========

If you want to contribute, please use the usual GitHub workflow:

1. Clone the repository.
2. Hack on your clone.
3. Send a pull request for review.

If you do not have programming skills, you can still contribute by `reporting
issues <https://github.com/aperezdc/gnarl/issues>`_ that you may
encounter.


Users
=====

The following projects make use of Gnarl |gnarl-icon|:

* `intheam-python <https://github.com/aperezdc/intheam-python>`__
* `pebbletime-python <https://github.com/aperezdc/pebbletime-python>`__

(If you use it, please do not hesitate in editing this file and add a line to
this list.)

