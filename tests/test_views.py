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
        view = self._test_view()
        assert view._query_params['_limit'] == 20

    def test_clean_id_name(self):
        view = self._test_view()
        view._resource = Mock(id_name='foo')
        assert view.clean_id_name == 'foo'
        view._resource = Mock(id_name='foo_bar')
        assert view.clean_id_name == 'bar'

    def test_resolve_kw(self):
        view = self._test_view()
        kwargs = {'foo_bar_qoo': 1, 'arg_val': 4, 'q': 3}
        assert view.resolve_kw(kwargs) == {'bar_qoo': 1, 'val': 4, 'q': 3}

    def test_location(self):
        view = self._test_view()
        view._resource = Mock(id_name='myid', uid='items')
        view._location(Mock(myid=123))
        view.request.route_url.assert_called_once_with(
            'items', myid=123)

    def test_location_split_id(self):
        view = self._test_view()
        view._resource = Mock(id_name='items_myid', uid='items')
        view._location(Mock(myid=123))
        view.request.route_url.assert_called_once_with(
            'items', items_myid=123)

    def test_get_collection_has_parent(self):
        view = self._test_view()
        view._parent_queryset = Mock(return_value=[1, 2, 3])
        view.Model = Mock()
        view.get_collection(name='ok')
        view._parent_queryset.assert_called_once_with()
        view.Model.filter_objects.assert_called_once_with(
            [1, 2, 3], _limit=20, foo='bar', name='ok')

    def test_get_collection_has_parent_empty_queryset(self):
        view = self._test_view()
        view._parent_queryset = Mock(return_value=[])
        view.Model = Mock()
        view.get_collection(name='ok')
        view._parent_queryset.assert_called_once_with()
        view.Model.filter_objects.assert_called_once_with(
            [], _limit=20, foo='bar', name='ok')

    def test_get_collection_no_parent(self):
        view = self._test_view()
        view._parent_queryset = Mock(return_value=None)
        view.Model = Mock()
        view.get_collection(name='ok')
        view._parent_queryset.assert_called_once_with()
        assert not view.Model.filter_objects.called
        view.Model.get_collection.assert_called_once_with(
            _limit=20, foo='bar', name='ok')

    def test_get_item_no_parent(self):
        view = self._test_view()
        view._parent_queryset = Mock(return_value=None)
        view.context = 1
        assert view.get_item(name='wqe') == 1

    def test_get_item_not_found_in_parent(self):
        view = self._test_view()
        view.Model = Mock(__name__='foo')
        view._get_context_key = Mock(return_value='123123')
        view._parent_queryset = Mock(return_value=[2, 3])
        view.context = 1
        with pytest.raises(JHTTPNotFound):
            view.get_item(name='wqe')

    def test_get_item_found_in_parent(self):
        view = self._test_view()
        view._parent_queryset = Mock(return_value=[1, 3])
        view.context = 1
        assert view.get_item(name='wqe') == 1

    def test_get_item_found_in_parent_context_callable(self):
        func = lambda x: x
        view = self._test_view()
        view._parent_queryset = Mock(return_value=[func, 3])
        view.reload_context = Mock()
        view.context = func
        assert view.get_item(name='wqe') is view.context
        view.reload_context.assert_called_once_with(
            es_based=False, name='wqe')

    def test_get_context_key(self):
        view = self._test_view()
        view._resource = Mock(id_name='foo')
        assert view._get_context_key(foo='bar') == 'bar'

    def test_parent_queryset(self):
        from pyramid.config import Configurator
        from ramses.acl import BaseACL
        config = Configurator()
        config.include('nefertari')
        root = config.get_root_resource()

        class View(self.view_cls, BaseView):
            _json_encoder = 'foo'

        user = root.add(
            'user', 'users', id_name=