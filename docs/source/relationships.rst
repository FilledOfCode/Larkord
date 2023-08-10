Relationships
=============


Basics
------

Relationships in Ramses are used to represent One-To-Many(o2m) and One-To-One(o2o) relationships between objects in database.

To set up relationships fields of types ``foreign_key`` and ``relationship`` are used. ``foreign_key`` field is not required when using ``nefertari_mongodb`` engine and is ignored.


For this tutorial we are going to use the example of users and
stories. In this example we have a OneToMany relationship betweed ``User``
and ``Story``. One user may have many stories but each story has only one
owner.  Check the end of the tutorial for the complete example RAML
file and schemas.

Example code is the very minimum needed to explain the subject. We will be referring to the examples along all the tutorial.


Field "type": "relationship"
----------------------------

Must be defined on the *One* side of OneToOne or OneToMany
relationship (``User`` in our example). Relationships are created as
OneToMany by default.

Example of using ``relationship`` field (defined on ``User`` model in our example):

.. code-block:: json

    "stories": {
        "_db_settings": {
            "type": "relationship",
            "document": "Story",
            "backref_name": "owner"
        }
    }

**Required params:**

*type*
    String. Just ``relationship``.

*document*
    String. Exact name of model class to which relationship is set up. To find out the name of model use singularized uppercased version of route name. E.g. if we want to set up relationship to objects of ``/stories`` then the ``document`` arg will be ``Story``.

*backref_name*
    String. Name of *back reference* field. This field will be auto-generated on model we set up relationship to and will hold the instance of model we are defining. In our example, field ``Story.owner`` will be generated and it will hold instance of ``User`` model to which story instance belongs. **Use this field to change relationships between objects.**


Field "type": "foreign_key"
---------------------------

This represents a Foreign Key constraint in SQL and is only required
when using ``nefertari_sqla`` engine. It is used in conjunction with
the relationship field, but is used on the model that ``relationship``
refers to. For example, if the ``User`` model contained the
``relationship`` field, than the ``Story`` model would need a
``foreign_key`` field.

**Notes:**

    * This field is not required and is ignored when using nefertari_mongodb engine.
    * Name of the ``foreign_key`` field does not depend on relationship params in any way.
    * This field **MUST NOT** be used to change relationships. This field only exists because it is required by SQLAlchemy.


Example of using ``fo