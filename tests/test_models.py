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
  