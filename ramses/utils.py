
import re
import logging
from contextlib import contextmanager

import six
import inflection


log = logging.getLogger(__name__)


class ContentTypes(object):
    """ ContentType values.

    """
    JSON = 'application/json'
    TEXT_XML = 'text/xml'
    MULTIPART_FORMDATA = 'multipart/form-data'
    FORM_URLENCODED = 'application/x-www-form-urlencoded'


def convert_schema(raml_schema, mime_type):
    """ Restructure `raml_schema` to a dictionary that has 'properties'
    as well as other schema keys/values.

    The resulting dictionary looks like this::

    {
        "properties": {
            "field1": {