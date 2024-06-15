import pytest
from mock import Mock, patch

from nefertari.json_httpexceptions import (
    JHTTPNotFound, JHTTPMethodNotAllowed)
from nefertari.view import BaseView

from ramses import views
from .fixtures import config_mock, guards_engine_mock


class ViewTestBase(obj