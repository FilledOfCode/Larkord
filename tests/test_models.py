import pytest
from mock import Mock, patch, call

from .fixtures import engine_mock, config_mock, guards_engine_mock


@pytest.mark.usefixtures('engine_mock')
class TestHelperFunctions(object):

    @patch('ramses.models.engine')
    def test_get_existing_model_not_found(self, mock_eng):
        from ramses import models
        mock_eng.get_document_cls.side_effect = ValueError
        model_cls = models.get_existing_model('Foo')
        assert model_cls is None
        mock_eng.get_document_cls.assert_called_once_with('Foo')

    @patch('ramses.models.engine')
    def test_get_existing_model_found(self, mock_eng):
        from ramses import models
        mock_eng.get_document_cls.return_value = 1
        model_cls = models.get_existing_model('Foo')
        assert model_cls == 1
        mock_eng.get_document_cls.assert_called_once_with('Foo')

    @patch('ramses.models.setup_data_model')
    @patch('ramses.models.get_existing_model')
    def test_prepare_relationship_model_exists(self, mock_get, mock_set):
        from ramses import models
        config = Mock()
        models.prepare_relationship(
            config, 'Story', 'raml_resource')
        mock_get.assert_called_once_with('Story')
        assert not mock_set.called

    @patch('ramses.models.get_existing_model')
    def test_prepare_relationship_resource_not_found(self, mock_get):
        from ramses import models
        config = Mock()
        resource = Mock(root=Mock(resources=[
            Mock(method='get', path='/stories'),
            Mock(method='options', path='/stories'),
            Mock(method='post', path='/items'),
        ]))
        mock_get.return_value = None
        with pytest.raises(ValueError) as ex:
            models.prepare_relationship(config, 'Story', resource)
        expected = ('Model `Story` used in relationship '
                    'is not defined')
        assert str(ex.value) == expected

    @patch('ramses.models.setup_data_model')
    @patch('ramses.models.get_existing_model')
    def test_prepare_relationship_resource_found(
            self, mock_get, mock_set):
        from ramses import models
        config = Mock()
        matching_res = Mock(method='post', path='/stories')
        resource = Mock(root=Mock(resources=[
            matching_res,
            Mock(method='options', path='/stories'),
            Mock(method='post', path='/items'),
        ]))
        mock_get.return_value = None
        config = config_mock()
        models.prepare_relationship(config, 'Story', resource)
        mock_set.assert_called_once_with(config, matching_res, 'Story')

    @patch('ramses.models.resource_schema')
    @patch('ramses.models.get_existing_model')
    def test_setup_data_model_existing_model(self, mock_get, mock_schema):
        from ramses import models
        config = Mock()
        mock_get.return_value = 1
        mock_schema.return_value = {"foo": "bar"}
        model, auth_model = models.setup_data_model(config, 'foo', 'Bar')
        assert not auth_model
        assert model == 1
        mock_get.assert_called_once_with('Bar')

    @patch('ramses.models.resource_schema')
    @patch('ramses.models.get_existing_model')
    def test_setup_data_model_existing_auth_model(self, mock_get, mock_schema):
        from ramses import models
        config = Mock()
        mock_get.return_value = 1
        mock_schema.return_value = {"_auth_model": True}
        model, auth_model = models.setup_data_model(config, 'foo', 'Bar')
        assert auth_model
        assert model == 1
        mock_get.assert_called_once_with('Bar')

    @patch('ramses.models.resource_schema')
    @patch('ramses.models.get_existing_model')
    def test_setup_data_model_no_schema(self, mock_get, mock_schema):
        from ramses import models
        config = Mock()
        mock_get.return_value = None
        mock_schema.return_value = None
        with pytest.raises(Exception) as ex:
            models.setup_data_model(config, 'foo', 'Bar')
        assert str(ex.value) == 'Missing schema for model `Bar`'
        mock_get.assert_called_once_with('Bar')
        mock_schema.assert_called_once_with('foo')

    @patch('ramses.models.resource_schema')
    @patch('ramses.models.generate_model_cls')
    @patch('ramses.models.get_existing_model')
    def test_setup_data_model_success(self, mock_get, mock_gen, mock_schema):
        from ramses import models
        mock_get.return_value = None
        mock_schema.return_value = {'field1': 'val1'}
        config = config_mock()
        model = models.setup_data_model(config, 'foo', 'Bar')
        mock_get.assert_called_once_with('Bar')
        mock_schema.assert_called_once_with('foo')
        mock_gen.assert_called_once_with(
            config,
            schema={'field1': 'val1'},
            model_name='Bar',
            raml_resource='foo')
        assert model == mock_gen()

    @patch('ramses.models.setup_data_model')
    def test_handle_model_generation_value_err(self, mock_set):
        from ramses import models
        config = Mock()
        mock_set.side_effect = ValueError('strange error')
        config = config_mock()
        with pytest.raises(ValueError) as ex:
            raml_resource = Mock(path='/stories')
            models.handle_model_generation(config, raml_resource)
        assert str(ex.value) == 'Story: strange error'
        mock_set.assert_called_once_with(config, raml_resource, 'Story')

    @patch('ramses.models.setup_data_model')
    def test_handle_model_generation(self, mock_set):
        from ramses import models
        config = Mock()
        mock_set.return_value = ('Foo1', True)
        config = config_mock()
        raml_resource = Mock(path='/stories')
        model, auth_model = models.handle_model_generation(
            config, raml_resource)
        mock_set.assert_called_once_with(config, raml_resource, 'Story')
        assert model == 'Foo1'
        assert auth_model


@patch('ramses.models.setup_fields_processors')
@patch('ramses.models.setup_model_event_subscribers')
@patch('ramses.models.registry')
@pytest.mark.usefixtures('engine_mock')
class T