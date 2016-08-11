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

import copy

from tuning_box import db
from tuning_box.library import components
from tuning_box.tests.test_app import BaseTest


class TestComponents(BaseTest):

    @property
    def _component_json(self):
        return {
            'id': 7,
            'name': 'component1',
            'resource_definitions': [{
                'id': 5,
                'name': 'resdef1',
                'component_id': 7,
                'content': {'key': 'nsname.key'},
            }],
        }

    def test_get_components_empty(self):
        res = self.client.get('/components')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_components(self):
        self._fixture()
        res = self.client.get('/components')
        self.assertEqual(200, res.status_code)
        self.assertItemsEqual(self._component_json, res.json[0])

    def test_get_one_component(self):
        self._fixture()
        res = self.client.get('/components/7')
        self.assertEqual(200, res.status_code)
        self.assertItemsEqual(self._component_json, res.json)

    def test_get_one_component_404(self):
        res = self.client.get('/components/7')
        self.assertEqual(res.status_code, 404)

    def test_post_component(self):
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        json['name'] = 'component2'
        res = self.client.post('/components', data=json)
        self.assertEqual(201, res.status_code)
        json['id'] = res.json['id']
        json['resource_definitions'][0]['component_id'] = json['id']
        json['resource_definitions'][0]['id'] = 6
        self.assertEqual(res.json, json)
        self._assert_db_effect(db.Component, res.json['id'],
                               components.component_fields, json)

    def test_post_component_conflict(self):
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 409)
        self._assert_not_in_db(db.Component, 8)

    def test_post_component_conflict_propagate_exc(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 409)
        self._assert_not_in_db(db.Component, 8)

    def test_post_component_no_resdef_content(self):
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        del json['resource_definitions'][0]['content']
        json['name'] = 'component2'
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = res.json['id']
        json['resource_definitions'][0]['component_id'] = json['id']
        json['resource_definitions'][0]['id'] = 6
        json['resource_definitions'][0]['content'] = None
        self.assertItemsEqual(json, res.json)
        self._assert_db_effect(db.Component, res.json['id'],
                               components.component_fields, json)

    def test_delete_component(self):
        self._fixture()
        res = self.client.delete('/components/7')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        self._assert_not_in_db(db.Component, 7)

    def test_delete_component_404(self):
        res = self.client.delete('/components/7')
        self.assertEqual(res.status_code, 404)

    def test_put_component_404(self):
        res = self.client.put('/components/7')
        self.assertEqual(res.status_code, 404)

    def test_put_component(self):
        self._fixture()
        component_url = '/components/7'
        initial_data = self._component_json
        new_name = 'new_{0}'.format(initial_data['name'])

        # Updating name
        res = self.client.put(component_url, data={'name': new_name})
        self.assertEqual(204, res.status_code)
        actual_component = self.client.get(component_url).json
        self.assertEqual(new_name, actual_component['name'])
        self.assertItemsEqual(initial_data['resource_definitions'],
                              actual_component['resource_definitions'])

        # Updating resource_definitions
        res = self.client.put(component_url,
                              data={'resource_definitions': []})
        self.assertEqual(204, res.status_code)
        actual_component = self.client.get(component_url).json
        self.assertEqual([], actual_component['resource_definitions'])

        # Restoring resource_definitions and name
        res = self.client.put(
            component_url,
            data={'name': initial_data['name'],
                  'resource_definitions': initial_data['resource_definitions']}
        )
        self.assertEqual(204, res.status_code)
        actual_component = self.client.get(component_url).json
        self.assertEqual(initial_data['name'],
                         actual_component['name'])
        self.assertItemsEqual(initial_data['resource_definitions'],
                              actual_component['resource_definitions'])

    def test_put_component_resource_not_found(self):
        self._fixture()
        component_url = '/components/7'
        initial_data = self._component_json

        resource_definition = copy.deepcopy(
            initial_data['resource_definitions'][0])
        resource_definition['id'] = None

        res = self.client.put(
            component_url,
            data={'resource_definitions': [resource_definition]}
        )
        self.assertEqual(404, res.status_code)

    def test_put_component_ignore_changing_id(self):
        self._fixture()
        component_url = '/components/7'
        initial_data = self._component_json
        new_name = 'new_{0}'.format(initial_data['name'])

        res = self.client.put(component_url,
                              data={'name': new_name, 'id': None,
                                    'fake': 'xxxx'})
        self.assertEqual(204, res.status_code)
        actual_component = self.client.get(component_url).json
        self.assertEqual(new_name, actual_component['name'])
        self.assertItemsEqual(initial_data['resource_definitions'],
                              actual_component['resource_definitions'])
