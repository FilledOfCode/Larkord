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

.. code-block:: j