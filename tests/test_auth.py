
import pytest
from mock import Mock, patch

from nefertari.utils import dictset
from pyramid.security import Allow, ALL_PERMISSIONS

from .fixtures import engine_mock, guards_engine_mock


@pytest.mark.usefixtures('engine_mock')
class TestACLAssignRegisterMixin(object):
    def _dummy_view(self):
        from ramses import auth

        class DummyBase(object):
            def register(self, *args, **kwargs):
                return 1

        class DummyView(auth.ACLAssignRegisterMixin, DummyBase):
            def __init__(self, *args, **kwargs):
                super(DummyView, self).__init__(*args, **kwargs)
                self.Model = Mock()
                self.request = Mock(_user=Mock())
                self.request.registry._model_collections = {}
        return DummyView

    def test_register_acl_present(self):
        DummyView = self._dummy_view()
        view = DummyView()
        view.request._user._acl = ['a']
        assert view.register() == 1
        assert view.request._user._acl == ['a']

    def test_register_no_model_collection(self):
        DummyView = self._dummy_view()
        view = DummyView()
        view.Model.__name__ = 'Foo'
        view.request._user._acl = []
        assert view.register() == 1
        assert view.request._user._acl == []

    def test_register_acl_set(self, guards_engine_mock):
        DummyView = self._dummy_view()
        view = DummyView()
        view.Model.__name__ = 'Foo'
        resource = Mock()
        view.request.registry._model_collections['Foo'] = resource
        view.request._user._acl = []
        assert view.register() == 1
        factory = resource.view._factory
        factory.assert_called_once_with(view.request)
        factory().generate_item_acl.assert_called_once_with(
            view.request._user)
        guards_engine_mock.ACLField.stringify_acl.assert_called_once_with(
            factory().generate_item_acl())
        view.request._user.update.assert_called_once_with(
            {'_acl': guards_engine_mock.ACLField.stringify_acl()})


@pytest.mark.usefixtures('engine_mock')
class TestSetupTicketPolicy(object):

    def test_no_secret(self):
        from ramses import auth
        with pytest.raises(ValueError) as ex:
            auth._setup_ticket_policy(config='', params={})
        expected = 'Missing required security scheme settings: secret'
        assert expected == str(ex.value)

    @patch('ramses.auth.AuthTktAuthenticationPolicy')
    def test_params_converted(self, mock_policy):
        from ramses import auth
        params = dictset(
            secure=True,
            include_ip=True,
            http_only=False,
            wild_domain=True,
            debug=True,
            parent_domain=True,
            secret='my_secret_setting'
        )
        auth_model = Mock()
        config = Mock()
        config.registry.settings = {'my_secret_setting': 12345}
        config.registry.auth_model = auth_model
        auth._setup_ticket_policy(config=config, params=params)
        mock_policy.assert_called_once_with(
            include_ip=True, secure=True, parent_domain=True,
            callback=auth_model.get_groups_by_userid, secret=12345,
            wild_domain=True, debug=True, http_only=False
        )

    @patch('ramses.auth.AuthTktAuthenticationPolicy')
    def test_request_method_added(self, mock_policy):
        from ramses import auth
        config = Mock()
        config.registry.settings = {'my_secret': 12345}
        config.registry.auth_model = Mock()
        policy = auth._setup_ticket_policy(
            config=config, params={'secret': 'my_secret'})
        config.add_request_method.assert_called_once_with(
            config.registry.auth_model.get_authuser_by_userid,
            'user', reify=True)
        assert policy == mock_policy()

    @patch('ramses.auth.AuthTktAuthenticationPolicy')
    def test_routes_views_added(self, mock_policy):
        from ramses import auth
        config = Mock()
        config.registry.settings = {'my_secret': 12345}
        config.registry.auth_model = Mock()
        root = Mock()
        config.get_root_resource.return_value = root
        auth._setup_ticket_policy(
            config=config, params={'secret': 'my_secret'})
        assert root.add.call_count == 3
        login, logout, register = root.add.call_args_list
        login_kwargs = login[1]
        assert sorted(login_kwargs.keys()) == sorted([
            'view', 'prefix', 'factory'])
        assert login_kwargs['prefix'] == 'auth'
        assert login_kwargs['factory'] == 'nefertari.acl.AuthenticationACL'

        logout_kwargs = logout[1]
        assert sorted(logout_kwargs.keys()) == sorted([
            'view', 'prefix', 'factory'])
        assert logout_kwargs['prefix'] == 'auth'
        assert logout_kwargs['factory'] == 'nefertari.acl.AuthenticationACL'

        register_kwargs = register[1]
        assert sorted(register_kwargs.keys()) == sorted([
            'view', 'prefix', 'factory'])
        assert register_kwargs['prefix'] == 'auth'
        assert register_kwargs['factory'] == 'nefertari.acl.AuthenticationACL'


@pytest.mark.usefixtures('engine_mock')
class TestSetupApiKeyPolicy(object):

    @patch('ramses.auth.ApiKeyAuthenticationPolicy')
    def test_policy_params(self, mock_policy):
        from ramses import auth
        auth_model = Mock()