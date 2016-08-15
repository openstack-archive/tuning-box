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

from tuning_box import errors
from tuning_box import library
from tuning_box.tests.test_app import BaseTest


class TestLibrary(BaseTest):

    def add_res_def_to_another_env(self, res_name):
        component_data = {
            'name': 'component2',
            'resource_definitions': [{
                'name': res_name,
                'content': {'key': 'value'}
            }]
        }
        res = self.client.post('/components', data=component_data)
        self.assertEqual(201, res.status_code)
        component_id = res.json['id']

        env_data = {
            'components': [component_id],
            'hierarchy_levels': [],
        }
        res = self.client.post('/environments', data=env_data)
        self.assertEqual(201, res.status_code)

    def test_get_resource_definition(self):
        self._fixture()
        res_name = 'resdef1'
        res_id = 5
        environment_id = 9
        component_id = 7

        # Creating resource definition with the same name in another
        # environment
        self.add_res_def_to_another_env(res_name)
        res = self.client.get('/resource_definitions')
        self.assertEqual(200, res.status_code)
        self.assertTrue(all(res_def['name'] == res_name
                            for res_def in res.json))

        with self.app.app_context():
            self.assertRaises(errors.TuningboxNotFound,
                              library.get_resource_definition, res_id, None)
            self.assertRaises(errors.TuningboxNotFound,
                              library.get_resource_definition, res_name, None)
            self.assertRaises(errors.TuningboxNotFound,
                              library.get_resource_definition, '',
                              environment_id)
            self.assertRaises(errors.TuningboxNotFound,
                              library.get_resource_definition, None, None)
            self.assertRaises(errors.TuningboxNotFound,
                              library.get_resource_definition, None,
                              environment_id)

            actual_res = library.get_resource_definition(res_id,
                                                         environment_id)
            self.assertEqual(res_id, actual_res.id)
            self.assertEqual(res_name, actual_res.name)
            self.assertEqual(component_id, actual_res.component_id)

            actual_res = library.get_resource_definition(res_id,
                                                         environment_id)
            self.assertEqual(res_id, actual_res.id)
            self.assertEqual(res_name, actual_res.name)
            self.assertEqual(component_id, actual_res.component_id)
