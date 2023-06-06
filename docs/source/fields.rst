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
