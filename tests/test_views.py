import pytest
from mock import Mock, patch

from nefertari.json_httpexceptions import (
    JHTTPNotFound, JHTTPMethodNotAllowed)
from nefertari.view import BaseView

from ramses import views
from .fixtures import config_mock, guards_engine_mock


class ViewTestBase(object):
    view_cls = None
    view_kwargs = dict(
        context={},
        _query_params={'foo': 'bar'},
        _json_params={'foo2': 'bar2'},
    )
    request_kwargs = dict(
        method='GET',
        accept=[''],
    )

    def _test_view(self):
        class View(self.view_cls, BaseView):
            _json_encoder = 'foo'

        request = Mock(**self.request_kwargs)
        return View(request=request, **self.view_kwargs)


class TestSetObjectACLMixin(object):
    def test_set_object_acl(self, guards_engine_mock):
        view = views.SetObjectACLMixin()
        view.request = 'foo'
        view._factory = Mock()
        obj = Mock(_acl=None)
        view.set_object_acl(obj)
        view._factory.assert_called_once_with(view.request)
        view._factory().generate_item_acl.assert_called_once_with(obj)
        field = guards_engine_mock.ACLField
        field.stringify_acl.assert_called_once_with(
            view._factory().generate_item_acl())
        assert obj._acl == field.stringify_acl()


class TestBaseView(ViewTestBase):
    view_cls = views.BaseView

    def test_init(self):
        view = self._test_v