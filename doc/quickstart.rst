============
 Quickstart
============

This guide will walk you through the basics of creating Gnarl schemas.


Declaring Schemas
=================

Let's start with a basic “user” model. Inheriting from :class:`Schemed` allows
to define a schema:

    >>> import gnarl
    >>> class User(gnarl.Schemed):
    ...     __schema__ = {
    ...         "name"       : str,
    ...         "email"      : str,  # Not a very thorough validation
    ...         "created_at" : gnarl.Timestamp,
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
`Delorean <http://delorean.readthedocs.io/en/latest/>`_ module:

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
   Delorean(datetime=datetime.datetime(1983, 5, 11, 19, 35), timezone='UTC')

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
   gnarl.SchemaError: 32 should be instance of <class 'str'>

Validation will be also carried on at object instantiation:

   >>> User(name=32, email="a@b.com", created_at="2015-09-30")
   ...
   Traceback (most recent call last):
      ...
   gnarl.SchemaError: 32 should be instance of <class 'str'>


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


HiPack Serialization
====================

If you have the `hipack module <https://pypi.python.org/pypi/hipack>`__
installed (it is an optional dependency, Gnarl will work just fine without
it), it is also possible to serialize objects to `HiPack
<http://hipack.org>`__, using the :func:`Schemed.to_hipack()` method.
Deserialization and validation can be done using the
:func:`Schemed.from_hipack()` class method.


Collections
===========

Schemas may contain nested lists and dictionaries. Let's change our ``User``
class to allow multiple e-mail addresses:

   >>> class User(gnarl.Schemed):
   ...     __schema__ = {
   ...          "name": str,
   ...          "emails": [str],  # A list of strings.
   ...     }
   ...
   >>> jdoe = User(name="John Doe",
   ...             emails=["jdoe@spammail.com", "john@doe.org"])
   ...
   >>> jdoe.emails
   ['jdoe@spammail.com', 'john@doe.org']

Dictionaries work as expected, but note that all keys and the types of their
associated values are fully type-checked:

   >>> class User(gnarl.Schemed):
   ...     __schema__ = { "name": { "first": str, "family": str } }
   ...
   >>> jdoe = User(name=dict(first="John", family="Doe"))
   >>> sorted(jdoe.name.items())
   [('family', 'Doe'), ('first', 'John')]



Better Validation
=================

Remember that e-mail addresses were not being verified for correctness? Gnarl
can automate additional validation for us as well. First, let's define a
validation function for e-mail addresses:

   >>> def validate_email(email):
   ...     if "@" not in email:  # Naïve check
   ...         raise gnarl.SchemaError("{!r} does not contain @".format(email))
   ...     return email
   ...

The :class:`gnarl.Use` helper class can be used to wrap a validation function
and use it as part of the schema. We still want to ensure that the value is a
string, and so :class:`gnarl.And` is used to instruct the validation engine to
ensure that the value is a string, *and* that the validation function does not
raise an error:

   >>> class User(gnarl.Schemed):
   ...     __schema__ = {
   ...         "name": str,
   ...         "email": gnarl.And(str, validate_email),
   ...     }
   ...

Now, using an invalid e-mail address will result in an error, even if the
value is a string:

   >>> jdoe = User(name="John Doe", email="invalid address")
   Traceback (most recent call last):
      ...
   gnarl.SchemaError: 'invalid address' does not contain @



Nesting Schemas
===============

It is possible to use a subclass of :class:`gnarl.Schemed` as an schema type
itself. This allows to construct schemas in which attributes can be themselves
type-checked objects. In our example, we could define the ``name`` attribute
to be an object with separate attributes for the surname and the family name:

   >>> class Name(gnarl.Schemed):
   ...     __schema__ = { "first": str, "family": str }
   ...
   >>> class User(gnarl.Schemed):
   ...     __schema__ = { "name": Name, "email": str }
   ...

Instantiating objects gets a little bit more involved, though the way things
work is still logical:

   >>> jdoe = User(name=Name(first="John", family="Doe"),
   ...             email="j@doe.org")
   ...

Serialization of nested schemas works as expected, using nested JSON
dictionaries for the child objects:

   >>> print(jdoe.to_json(sort_keys=True, indent=4))
   {
       "email": "j@doe.org",
       "name": {
           "family": "Doe",
           "first": "John"
       }
   }

Loading a JSON snippet also works as expected when using nested schemas:

   >>> monty = User.from_json("""\
   ... { "email": "monty@spam.org", "name": {
   ...   "first": "Monty", "family": "Python" }}""")
   ...
   >>> isinstance(monty.name, Name)
   True
   >>> monty.email, monty.name.first, monty.name.family
   ('monty@spam.org', 'Monty', 'Python')

