============
 Quickstart
============

This guide will walk you through the basics of creating Lasso schemas.


Declaring Schemas
=================

Let's start with a basic “user” model. Inheriting from :class:`Schemed` allows
to define a schema:

    >>> import lasso
    >>> class User(lasso.Schemed):
    ...     __schema__ = {
    ...         "name"       : str,
    ...         "email"      : str,  # Not a very thorough validation
    ...         "created_at" : lasso.Timestamp,
    ...     }
    ...     def __repr__(self):
    ...         return "<User name={u.name!r}>".format(u=self)
    ...

The ``__schema__`` class attribute is a dictionary that defines the names
of the attributes of ``User`` instances, and their types.

We could have defined the ``email`` attribute in such a way that the e-mail
address would be checked for validity, but we will leave that for later.


Object Instantiation
====================

We can instantiate ``User`` normally, as long as the parameters to the
constructor are given as keyword arguments. The timestamp can be passed as a
string, and it will be parsed using the
`Delorean <http://delorean.readthedocs.org/en/latest/>`_ module:

   >>> jdoe = User(name="John Doe", email="jdoe@spammail.com",
   ...            created_at="1983-05-11 19:35:00 +0000")
   ...
   >>> jdoe
   <User name='John Doe'>

Note how the attributes declared in the schema are available using the normal
attribute syntax; the timestamp has been converted automatically into an
instance of the `Delorean
<http://delorean.readthedocs.org/en/latest/interface.html#module-delorean.dates>`_
class:

   >>> jdoe.name
   'John Doe'
   >>> jdoe.email
   'jdoe@spammail.com'
   >>> jdoe.created_at
   Delorean(datetime=1983-05-11 19:35:00+00:00, timezone=UTC)

The attributes can be modified normally as well:

   >>> jdoe.email = "johnny@doe.org"
   >>> jdoe.email
   'johnny@doe.org'


Data Validation
===============

Data contained in schema attributes are guaranteed to always contain valid
information of declared type. This means that assigning values of invalid
types to attributes will raise a :class:`SchemaError`:

   >>> jdoe.name = 32
   Traceback (most recent call last):
      ...
   schema.SchemaError: 32 should be instance of <class 'str'>

Validation will be also carried on at object instantiation:

   >>> User(name=32, email="a@b.com", created_at="2015-09-30")
   ...
   Traceback (most recent call last):
      ...
   schema.SchemaError: 32 should be instance of <class 'str'>


JSON Serialization
==================

Objects can be serialized to `JSON <http://json.org>`_ using the
:func:`Schemed.to_json()` method, which accepts the same keyword arguments as
the ``json.dumps()`` function from the standard library:

   >>> print(jdoe.to_json(sort_keys=True, indent=4))
   {
       "created_at": "1983-05-11T19:35:00+00:00",
       "email": "johnny@doe.org",
       "name": "John Doe"
   }

Conversely, the :func:`Schemed.from_json()` class method will do the opposite,
deserializing a JSON string and creating objects as needed:

   >>> u = User.from_json("""\
   ... { "name": "Monty", "email": "monty@python.org",
   ...   "created_at": "1991-10-11T20:00:00+00:00" }""")
   ...
   >>> u
   <User name='Monty'>

When deserializing data from JSON, input validation and conversion is done
exactly in the same way, always following the declared schema.

