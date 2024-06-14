
import pytest
from mock import Mock, patch

from ramses import utils


class TestUtils(object):

    def test_contenttypes(self):
        assert utils.ContentTypes.JSON == 'application/json'
        assert utils.ContentTypes.TEXT_XML == 'text/xml'
        assert utils.ContentTypes.MULTIPART_FORMDATA == \
            'multipart/form-data'
        assert utils.ContentTypes.FORM_URLENCODED == \
            'application/x-www-form-urlencoded'

    def test_convert_schema_json(self):
        schema = utils.convert_schema({'foo': 'bar'}, 'application/json')
        assert schema == {'foo': 'bar'}

    def test_convert_schema_json_error(self):
        with pytest.raises(TypeError) as ex:
            utils.convert_schema('foo', 'application/json')
        assert 'Schema is not a valid JSON' in str(ex.value)

    def test_convert_schema_xml(self):
        assert utils.convert_schema({'foo': 'bar'}, 'text/xml') is None

    def test_is_dynamic_uri(self):
        assert utils.is_dynamic_uri('/{id}')
        assert not utils.is_dynamic_uri('/collection')

    def test_clean_dynamic_uri(self):
        clean = utils.clean_dynamic_uri('/{item_id}')
        assert clean == 'item_id'

    def test_generate_model_name(self):
        resource = Mock(path='/zoo/alien-users')
        model_name = utils.generate_model_name(resource)
        assert model_name == 'AlienUser'

    @patch.object(utils, 'get_resource_children')
    def test_dynamic_part_name(self, get_children):
        get_children.return_value = [
            Mock(path='/items'), Mock(path='/{myid}')]
        resource = Mock()
        part_name = utils.dynamic_part_name(
            resource, 'stories', 'default_id')
        assert part_name == 'stories_myid'
        get_children.assert_called_once_with(resource)

    @patch.object(utils, 'get_resource_children')
    def test_dynamic_part_name_no_dynamic(self, get_children):
        get_children.return_value = [Mock(path='/items')]
        resource = Mock()
        part_name = utils.dynamic_part_name(
            resource, 'stories', 'default_id')
        assert part_name == 'stories_default_id'
        get_children.assert_called_once_with(resource)

    @patch.object(utils, 'get_resource_children')
    def test_dynamic_part_name_no_resources(self, get_children):
        get_children.return_value = []
        resource = Mock(resources=None)
        part_name = utils.dynamic_part_name(
            resource, 'stories', 'default_id')
        assert part_name == 'stories_default_id'
        get_children.assert_called_once_with(resource)

    def test_extract_dynamic_part(self):
        assert utils.extract_dynamic_part('/stories/{id}/foo') == 'id'
        assert utils.extract_dynamic_part('/stories/{id}') == 'id'

    def test_extract_dynamic_part_fail(self):
        assert utils.extract_dynamic_part('/stories/id') is None
