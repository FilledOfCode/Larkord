Fields
======

Types
-----

You can set a field's type by setting the ``type`` property under ``_db_settings``.

.. code-block:: json

    "created_at": {
        (...)
        "_db_settings": {
            "type": "datetime"
        }
    }

This is a list of all available types:

* biginteger
* binary
* boolean
* choice
* date
* datetime
* decimal
* dict
* float
* foreign_key
* id_field
* integer
* interval
* list
* pickle
* relationship
* smallinteger
* string
* text
* time
* unicode
* unicodetext


Required Fields
---------------

You can set a field as required by setting the ``required`` property under ``_db_settings``.

.. code-block:: json

    "password": {
        (...)
        "_db_settings": {
            (...)
            "required": true
        }
    }


Primary Key
-----------

You can use an ``id_field`` in lieu of primary key.

.. code-block:: json

    "id": {
        (...)
        "_db_settings": {
            (...)
            "primary_key": true
        }
    }

You can alternatively elect a field to be the primary key of your model by setting its ``primary_key`` property under ``_db_settings``. For example, if you decide to use ``username`` as the primary key of your `User` model. This will enable resources to refer to that field in their url, e.g. ``/api/users/john``

.. code-block:: json

    "username": {
        (...)
        "_db_settings": {
            (...)
            "primary_key": true
        }
    }

Constraints
-----------

You can set a minimum and/or maximum length of your field by setting the ``min_length`` / ``max_length`` properties under ``_db_settings``. You can also add a unique constraint on a field by setting the ``unique`` property.

.. code-block:: json

    "field": {
        (...)
        "_db_settings": {
            (...)
            "unique": true,
            "min_length": 5,
            "max_length": 50
        }
    }


Default Value
-------------

You can set a default value for you field by setting the ``default`` pro