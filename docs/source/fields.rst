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
* dat