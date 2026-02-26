Kobject Documentation
=====================

Kobject is a Python runtime type validation library for classes and dataclasses.
It validates ``__init__`` parameter types at instantiation time, supporting Python 3.10+.

Features
--------

- **Runtime type validation** for ``__init__`` parameters
- **Zero runtime dependencies** - pure Python implementation
- **Dataclass support** - works seamlessly with ``@dataclass``
- **JSON serialization** - ``to_json()``, ``dict()``, ``from_json()``, ``from_dict()``
- **JSON Schema generation** - Draft 7 compliant schemas
- **Custom type resolvers** - extend for your own types
- **Thread-safe** - safe for concurrent use

Quick Start
-----------

.. code-block:: python

    from dataclasses import dataclass
    from kobject import Kobject

    @dataclass
    class User(Kobject):
        name: str
        age: int

    # Valid - passes type checking
    user = User(name="Alice", age=30)

    # Invalid - raises TypeError
    user = User(name="Alice", age="thirty")

Installation
------------

.. code-block:: bash

    pip install kobject

Contents
--------

.. toctree::
   :maxdepth: 2

   api
   changelog


API Reference
-------------

.. toctree::
   :maxdepth: 2

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
