# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tuning_box import db
from tuning_box.library import resource_definitions
from tuning_box.tests.test_app import BaseTest


class TestResourceDefinitions(BaseTest):

    collection_url = '/resource_definitions'
    object_url = '/resource_definition/{0}'
    object_keys_url = object_url + '/keys/{1}'

    @property
    def _resource_json(self):
        return {
            'id': 5,
            'name': 'resdef1',
            'component_id': 7,
            'content': {'key': 'nsname.key'},
        }

    def test_post_resource_definition(self):
        data = self._resource_json
        data['component_id'] = None

        res = self.client.post(self.collection_url, data=data)
        self.assertEqual(201, res.status_code)
        data['id'] = res.json['id']

        self.assertEqual(data, res.json)
        self._assert_db_effect(
            db.ResourceDefinition,
            res.json['id'],
            resource_definitions.resource_definition_fields,
            data
        )

    def test_get_resource_definitions_empty(self):
        res = self.client.get(self.collection_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_definitions(self):
        self._fixture()
        res = self.client.get(self.collection_url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.json))
        self.assertItemsEqual(self._resource_json, res.json[0])

    def test_get_definitions_filtration(self):
        self._fixture()

        resource_data = {
            'name': 'resdef2',
            'content': {'key': 'service.key'},
        }

        res = self.client.post(self.collection_url, data=resource_data)
        self.assertEqual(201, res.status_code)
        resource_data = res.json

        component_id = self._resource_json['component_id']
        res = self.client.get(self.collection_url,
                              query_string={'component_id': component_id})
        self.assertEqual(200, res.status_code)
        self.assertNotIn(resource_data['id'], (d['id'] for d in res.json))

        res = self.client.get(self.collection_url + '?component_id=')
        self.assertEqual(200, res.status_code)
        self.assertFalse(any(d['component_id'] for d in res.json))
        self.assertIn(resource_data['id'], (d['id'] for d in res.json))

        res = self.client.get(self.collection_url)
        self.assertEqual(200, res.status_code)
        self.assertIn(resource_data['id'], (d['id'] for d in res.json))
        self.assertIn(self._resource_json['id'], (d['id'] for d in res.json))

    def test_get_one_resource_definition(self):
        self._fixture()
        res_id = self._resource_json['id']
        res = self.client.get(self.object_url.format(res_id))
        self.assertEqual(200, res.status_code)
        self.assertItemsEqual(self._resource_json, res.json)

    def test_get_one_resource_definition_404(self):
        res_id = self._resource_json['id']
        res = self.client.get(
            self.object_url.format(res_id))
        self.assertEqual(res.status_code, 404)

    def test_delete_resource_definition(self):
        self._fixture()
        res_id = self._resource_json['id']
        res = self.client.delete(self.object_url.format(res_id))
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        self._assert_not_in_db(db.ResourceDefinition, res_id)

    def test_delete_resource_definition_404(self):
        res_id = self._resource_json['id']
        res = self.client.delete(self.object_url.format(res_id))
        self.assertEqual(res.status_code, 404)

    def test_put_resource_definition_404(self):
        res_id = self._resource_json['id']
        res = self.client.delete(self.object_url.format(res_id))
        self.assertEqual(res.status_code, 404)

    def test_put_resource_definition(self):
        self._fixture()
        res_id = self._resource_json['id']

        data = self._resource_json
        data['name'] = 'new_{0}'.format(data['name'])
        data['component_id'] = None
        data['content'] = {'x': 'y'}

        res = self.client.put(self.object_url.format(res_id),
                              data=data)
        self.assertEqual(204, res.status_code)
        actual_res_def = self.client.get(self.object_url.format(res_id)).json
        self.assertItemsEqual(data, actual_res_def)

        # Restoring resource_definition values
        res = self.client.put(
            self.object_url.format(res_id),
            data=self._resource_json
        )
        self.assertEqual(204, res.status_code)
        actual_res_def = self.client.get(self.object_url.format(res_id)).json
        self.assertItemsEqual(self._resource_json, actual_res_def)

    def test_put_resource_definition_ignore_changing_id(self):
        self._fixture()
        res_id = self._resource_json['id']

        data = self._resource_json
        data['id'] = None
        res = self.client.put(self.object_url.format(res_id), data=data)
        self.assertEqual(204, res.status_code)
        actual_res_def = self.client.get(self.object_url.format(res_id)).json
        self.assertItemsEqual(self._resource_json, actual_res_def)

    def test_put_resource_definition_set_operation_error(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        res_id = self._resource_json['id']

        data = [['a', 'b', 'c', 'value']]
        res = self.client.put(self.object_keys_url.format(res_id, 'set'),
                              data=data)
        self.assertEqual(409, res.status_code)

    def test_put_resource_definition_set(self):
        self._fixture()
        res_id = self._resource_json['id']

        data = [['key', 'key_value'], ['key_x', 'key_x_value']]
        res = self.client.put(self.object_keys_url.format(res_id, 'set'),
                              data=data)
        self.assertEqual(204, res.status_code)

        res = self.client.get(self.object_url.format(res_id))
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual({'key': 'key_value', 'key_x': 'key_x_value'},
                         actual['content'])
