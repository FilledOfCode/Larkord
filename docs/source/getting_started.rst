Getting started
===============

1. Create your project in a virtualenv directory (see the `virtualenv documentation <https://virtualenv.pypa.io>`_)

.. code-block:: shell

    $ virtualenv my_project
    $ source my_project/bin/activate
    $ pip install ramses
    $ pcreate -s ramses_starter my_project
    $ cd my_project
    $ pserve local.ini

2. Tada! Start editing api.raml to modify the API and items.json for the schema.


Requirements
------------

* Python 2.7, 3.3 or 3.4
* Elasticsearch (data is automatically indexed for near rea