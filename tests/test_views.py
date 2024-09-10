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
            'user', 'users', id_name='username',
            view=View, factory=BaseACL)
        user.add(
            'story', 'stories', id_name='prof_id',
            view=View, factory=BaseACL)
        view_cls = root.resource_map['user:story'].view
        view_cls._json_encoder = 'foo'

        request = Mock(
            registry=Mock(),
            path='/foo/foo',
            matchdict={'username': 'user12', 'prof_id': 4},
            accept=[''], method='GET'
        )
        request.params.mixed.return_value = {'foo1': 'bar1'}
        request.blank.return_value = request
        stories_view = view_cls(
            request=request,
            context={},
            _query_params={'foo1': 'bar1'},
            _json_params={'foo2': 'bar2'},)

        parent_view = stories_view._resource.parent.view
        with patch.object(parent_view, 'get_item') as get_item:
            parent_view.get_item = get_item
            result = stories_view._parent_queryset()
            get_item.assert_called_once_with(username='user12')
            assert result == get_item().stories

    def test_reload_context(self):
        class Factory(dict):
            item_model = None

            def __getitem__(self, key):
                return key

        view = self._test_view()
        view._factory = Factory
        view._get_context_key = Mock(return_value='foo')
        view.reload_context(es_based=False, arg='asd')
        view._get_context_key.assert_called_once_with(arg='asd')
        assert view.context == 'foo'


class TestCollectionView(ViewTestBase):
    view_cls = views.CollectionView

    def test_index(self):
        view = self._test_view()
        view.get_collection = Mock()
        resp = view.index(foo='bar')
        view.get_collection.assert_called_once_with()
        assert resp == view.get_collection()

    def test_show(self):
        view = self._test_view()
        view.get_item = Mock()
        resp = view.show(foo='bar')
        view.get_item.assert_called_once_with(foo='bar')
        assert resp == view.get_item()

    def test_create(self):
        view = self._test_view()
        view.set_object_acl = Mock()
        view.request.registry._root_resources = {
            'foo': Mock(auth=False)
        }
        view.Model = Mock()
        obj = Mock()
        obj.to_dict.return_value = {'id': 1}
        view.Model().save.return_value = obj
        view._location = Mock(return_value='/sadasd')
        resp = view.create(foo='bar')
        view.Model.assert_called_with(foo2='bar2')
        view.Model().save.assert_called_with(view.request)
        assert view.set_object_acl.call_count == 1
        assert resp == view.Model().save()

    def test_update(self):
        view = self._test_view()
        view.get_item = Mock()
        view._location = Mock(return_value='/sadasd')
        resp = view.update(foo=1)
        view.get_item.assert_called_once_with(foo=1)
        view.get_item().update.assert_called_once_with(
            {'foo2': 'bar2'}, view.request)
        assert resp == view.get_item().update()

    def test_replace(self):
        view = self._test_view()
        view.update = Mock()
        resp = view.replace(foo=1)
        view.update.assert_called_once_with(foo=1)
        assert resp == view.update()

    def test_delete(self):
        view = self._test_view()
        view.get_item = Mock()
        resp = view.delete(foo=1)
        view.get_item.assert_called_once_with(foo=1)
        view.get_item().delete.assert_called_once_with(
            view.request)
        assert resp is None

    def test_delete_many(self):
        view = self._test_view()
        view.Model = Mock(__name__='Mock')
        view.Model._delete_many.return_value = 123
        view.get_collection = Mock()
        resp = view.delete_many(foo=1)
        view.get_collection.assert_called_once_with()
        view.Model._delete_many.assert_called_once_with(
            view.get_collection(), view.request)
        assert resp == 123

    def test_update_many(self):
        view = self._test_view()
        view.Model = Mock(__name__='Mock')
        view.Model._update_many.return_value = 123
        view.get_collection = Mock()
        resp = view.update_many(qoo=1)
        view.get_collection.assert_called_once_with(_limit=20, foo='bar')
        view.Model._update_many.assert_called_once_with(
            view.get_collection(), {'foo2': 'bar2'},
            view.request)
        assert resp == 123


class TestESBaseView(ViewTestBase):
    view_cls = views.ESBaseView

    def test_parent_queryset_es(self):
        from pyramid.config import Configurator
        from ramses.acl import BaseACL

        class View(self.view_cls, BaseView):
            _json_encoder = 'foo'

        config = Configurator()
        config.include('nefertari')
        root = config.get_root_resource()
        user = root.add(
            'user', 'users', id_name='username',
            view=View, factory=BaseACL)
        user.add(
            'story', 'stories', id_name='prof_id',
            view=View, factory=BaseACL)
        view_cls = root.resource_map['user:story'].view
        view_cls._json_encoder = 'foo'

        request = Mock(
            registry=Mock(),
            path='/foo/foo',
            matchdict={'username': 'user12', 'prof_id': 4},
            accept=[''], method='GET'
        )
        request.params.mixed.return_value = {'foo1': 'bar1'}
        request.blank.return_value = request
        stories_view = view_cls(
            request=request,
            context={},
            _query_params={'foo1': 'bar1'},
            _json_params={'foo2': 'bar2'},)

        parent_view = stories_view._resource.parent.view
        with patch.object(parent_view, 'get_item_es') as get_item_es:
            parent_view.get_item_es = get_item_es
            result = stories_view._parent_queryset_es()
            get_item_es.assert_called_once_with(username='user12')
            assert result == get_item_es().stories

    def test_get_es_object_ids(self):
        view = self._test_view()
        view._resource = Mock(id_name='foobar')
        objects = [Mock(foobar=4), Mock(foobar=7)]
        assert sorted(view.get_es_object_ids(objects)) == ['4', '7']

    @patch('nefertari.elasticsearch.ES')
    def test_get_collection_es_no_parent(self, mock_es):
        mock_es.settings.asbool.return_value = False
        view = self._test_view()
        view._parent_queryset_es = Mock(return_value=None)
        view.Model = Mock(__name__='Foo')
        view.get_collection_es()
        mock_es.assert_called_once_with('Foo')
        mock_es().get_collection.assert_called_once_with(
            _limit=20, foo='bar')

    @patch('nefertari.elasticsearch.ES')
    def test_get_collection_es_parent_no_obj_ids(self, mock_es):
        mock_es.settings.asbool.return_value = False
        view = self._test_view()
        view._parent_queryset_es = Mock(return_value=[1, 2])
        view.Model = Mock(__name__='Foo')
        view.get_es_object_ids = Mock(return_value=None)
        result = view.get_collection_es()
        assert not mock_es().get_collection.called
        asse