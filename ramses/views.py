
import logging

import six
from nefertari.view import BaseView as NefertariBaseView
from nefertari.json_httpexceptions import JHTTPNotFound

from .utils import patch_view_model


log = logging.getLogger(__name__)

"""
Maps of {HTTP_method: neferteri view method name}

"""
collection_methods = {
    'get':      'index',
    'head':     'index',
    'post':     'create',
    'put':      'update_many',
    'patch':    'update_many',
    'delete':   'delete_many',
    'options':  'collection_options',
}
item_methods = {
    'get':      'show',
    'head':     'show',
    'post':     'create',
    'put':      'replace',
    'patch':    'update',
    'delete':   'delete',
    'options':  'item_options',
}


class SetObjectACLMixin(object):
    def set_object_acl(self, obj):
        """ Set object ACL on creation if not already present. """
        if not obj._acl:
            from nefertari_guards import engine as guards_engine
            acl = self._factory(self.request).generate_item_acl(obj)
            obj._acl = guards_engine.ACLField.stringify_acl(acl)


class BaseView(object):
    """ Base view class for other all views that defines few helper methods.

    Use `self.get_collection` and `self.get_item` to get access to set of
    objects and object respectively which are valid at current level.
    """
    @property
    def clean_id_name(self):
        id_name = self._resource.id_name
        if '_' in id_name:
            return id_name.split('_', 1)[1]
        else:
            return id_name

    def set_object_acl(self, obj):
        pass

    def resolve_kw(self, kwargs):
        """ Resolve :kwargs: like `story_id: 1` to the form of `id: 1`.

        """
        resolved = {}
        for key, value in kwargs.items():
            split = key.split('_', 1)
            if len(split) > 1:
                key = split[1]
            resolved[key] = value
        return resolved

    def _location(self, obj):
        """ Get location of the `obj`

        Arguments:
            :obj: self.Model instance.
        """
        field_name = self.clean_id_name
        return self.request.route_url(
            self._resource.uid,
            **{self._resource.id_name: getattr(obj, field_name)})

    def _parent_queryset(self):
        """ Get queryset of parent view.

        Generated queryset is used to run queries in the current level view.
        """
        parent = self._resource.parent
        if hasattr(parent, 'view'):
            req = self.request.blank(self.request.path)
            req.registry = self.request.registry
            req.matchdict = {
                parent.id_name: self.request.matchdict.get(parent.id_name)}
            parent_view = parent.view(parent.view._factory, req)
            obj = parent_view.get_item(**req.matchdict)
            if isinstance(self, ItemSubresourceBaseView):
                return
            prop = self._resource.collection_name
            return getattr(obj, prop, None)

    def get_collection(self, **kwargs):
        """ Get objects collection taking into account generated queryset
        of parent view.

        This method allows working with nested resources properly. Thus a
        queryset returned by this method will be a subset of its parent
        view's queryset, thus filtering out objects that don't belong to
        the parent object.
        """
        self._query_params.update(kwargs)
        objects = self._parent_queryset()
        if objects is not None:
            return self.Model.filter_objects(
                objects, **self._query_params)
        return self.Model.get_collection(**self._query_params)

    def get_item(self, **kwargs):
        """ Get collection item taking into account generated queryset
        of parent view.

        This method allows working with nested resources properly. Thus an item
        returned by this method will belong to its parent view's queryset, thus
        filtering out objects that don't belong to the parent object.

        Returns an object from the applicable ACL. If ACL wasn't applied, it is
        applied explicitly.
        """
        if six.callable(self.context):
            self.reload_context(es_based=False, **kwargs)

        objects = self._parent_queryset()
        if objects is not None and self.context not in objects:
            raise JHTTPNotFound('{}({}) not found'.format(
                self.Model.__name__,
                self._get_context_key(**kwargs)))

        return self.context

    def _get_context_key(self, **kwargs):
        """ Get value of `self._resource.id_name` from :kwargs: """
        return str(kwargs.get(self._resource.id_name))

    def reload_context(self, es_based, **kwargs):
        """ Reload `self.context` object into a DB or ES object.

        A reload is performed by getting the object ID from :kwargs: and then
        getting a context key item from the new instance of `self._factory`
        which is an ACL class used by the current view.

        Arguments:
            :es_based: Boolean. Whether to init ACL ac es-based or not. This
                affects the backend which will be queried - either DB or ES
            :kwargs: Kwargs that contain value for current resource 'id_name'
                key
        """
        from .acl import BaseACL
        key = self._get_context_key(**kwargs)
        kwargs = {'request': self.request}
        if issubclass(self._factory, BaseACL):
            kwargs['es_based'] = es_based

        acl = self._factory(**kwargs)
        if acl.item_model is None:
            acl.item_model = self.Model

        self.context = acl[key]


class CollectionView(BaseView):
    """ View that works with database and implements handlers for all
    available CRUD operations.

    """
    def index(self, **kwargs):
        return self.get_collection()

    def show(self, **kwargs):
        return self.get_item(**kwargs)

    def create(self, **kwargs):
        obj = self.Model(**self._json_params)
        self.set_object_acl(obj)
        return obj.save(self.request)

    def update(self, **kwargs):
        obj = self.get_item(**kwargs)
        return obj.update(self._json_params, self.request)

    def replace(self, **kwargs):
        return self.update(**kwargs)

    def delete(self, **kwargs):
        obj = self.get_item(**kwargs)
        obj.delete(self.request)

    def delete_many(self, **kwargs):
        objects = self.get_collection()
        return self.Model._delete_many(objects, self.request)

    def update_many(self, **kwargs):
        objects = self.get_collection(**self._query_params)
        return self.Model._update_many(
            objects, self._json_params, self.request)


class ESBaseView(BaseView):
    """ Elasticsearch base view that fetches data from ES.

    Implements analogues of _parent_queryset, get_collection, get_item
    fetching data from ES instead of database.

    Use `self.get_collection_es` and `self.get_item_es` to get access
    to the set of objects and individual object respectively which are
    valid at the current level.
    """
    def _parent_queryset_es(self):
        """ Get queryset (list of object IDs) of parent view.

        The generated queryset is used to run queries in the current level's
        view.
        """
        parent = self._resource.parent
        if hasattr(parent, 'view'):
            req = self.request.blank(self.request.path)
            req.registry = self.request.registry
            req.matchdict = {
                parent.id_name: self.request.matchdict.get(parent.id_name)}
            parent_view = parent.view(parent.view._factory, req)
            obj = parent_view.get_item_es(**req.matchdict)
            prop = self._resource.collection_name
            objects_ids = getattr(obj, prop, None)
            return objects_ids

    def get_es_object_ids(self, objects):