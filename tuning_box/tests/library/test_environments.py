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
from tuning_box.library import environments
from tuning_box.tests.test_app import BaseTest


class TestEnvironments(BaseTest):

    def test_get_environments_empty(self):
        res = self.client.get('/environments')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_environments(self):
        self._fixture()
        res = self.client.get('/environments')
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.json))
        self.assertItemsEqual(
            {'id': 9, 'components': [7], 'hierarchy_levels': ['lvl1', 'lvl2']},
            res.json[0]
        )

    def test_get_one_environment(self):
        self._fixture()
        res = self.client.get('/environments/9')
        self.assertEqual(200, res.status_code)
        self.assertItemsEqual(
            {'id': 9, 'components': [7], 'hierarchy_levels': ['lvl1', 'lvl2']},
            res.json
        )

    def test_get_one_environment_404(self):
        res = self.client.get('/environments/9')
        self.assertEqual(res.status_code, 404)

    def test_post_environment(self):
        self._fixture()
        json = {'components': [7], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = res.json['id']
        self.assertItemsEqual(json, res.json)
        self._assert_db_effect(
            db.Environment, res.json['id'],
            environments.environment_fields, json)

    def test_post_environment_preserve_id(self):
        self._fixture()
        json = {
            'id': 42,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(201, res.status_code)
        self.assertItemsEqual(json, res.json)
        self._assert_db_effect(
            db.Environment, 42, environments.environment_fields, json)

    def test_post_environment_preserve_id_conflict(self):
        self._fixture()
        json = {
            'id': 9,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 409)

    def test_post_environment_preserve_id_conflict_propagate_exc(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        json = {
            'id': 9,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 409)

    def test_post_environment_by_component_name(self):
        self._fixture()
        json = {
            'components': ['component1'],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = res.json['id']
        json['components'] = [7]
        self.assertItemsEqual(json, res.json)
        self._assert_db_effect(
            db.Environment, res.json['id'],
            environments.environment_fields, json)

    def test_post_components_duplication(self):
        self._fixture()
        json = {
            'components': ['component1', 7],
            'hierarchy_levels': ['lvl'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(409, res.status_code)

    def test_post_environment_404(self):
        self._fixture()
        json = {'components': [8], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 404)
        self._assert_not_in_db(db.Environment, 10)

    def test_post_environment_by_component_name_404(self):
        self._fixture()
        json = {
            'components': ['component2'],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 404)
        self._assert_not_in_db(db.Environment, 10)

    def test_delete_environment(self):
        self._fixture()
        res = self.client.delete('/environments/9')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        self._assert_not_in_db(db.Environment, 9)

    def test_delete_environment_404(self):
        res = self.client.delete('/environments/9')
        self.assertEqual(res.status_code, 404)

    def test_put_environment_404(self):
        res = self.client.put('/environments/7')
        self.assertEqual(res.status_code, 404)

    def test_put_environment_components(self):
        self._fixture()
        environment_url = '/environment/9'
        initial = self.client.get(environment_url).json

        # Updating components
        res = self.client.put(environment_url,
                              data={'components': []})
        self.assertEqual(204, res.status_code)
        actual = self.client.get(environment_url).json
        self.assertEqual([], actual['components'])

        # Restoring components
        res = self.client.put(
            environment_url,
            data={'components': initial['components']}
        )
        self.assertEqual(204, res.status_code)
        actual = self.client.get(environment_url).json
        self.assertItemsEqual(initial, actual)

    def test_put_environment_component_not_found(self):
        self._fixture()
        environment_url = '/environment/9'
        res = self.client.put(
            environment_url,
            data={'components': [None]}
        )
        self.assertEqual(404, res.status_code)

    def test_put_environment_hierarchy_levels(self):
        self._fixture()
        environment_url = '/environment/9'
        initial = self.client.get(environment_url).json

        # Updating hierarchy levels
        res = self.client.put(environment_url,
                              data={'hierarchy_levels': []})
        self.assertEqual(204, res.status_code)
        actual = self.client.get(environment_url).json
        self.assertEqual([], actual['hierarchy_levels'])

        # Restoring levels
        res = self.client.put(
            environment_url,
            data={'hierarchy_levels': initial['hierarchy_levels']}
        )
        self.assertEqual(204, res.status_code)
        actual = self.client.get(environment_url).json
        self.assertItemsEqual(initial, actual)

    def test_put_environment_level_not_found(self):
        self._fixture()
        environment_url = '/environment/9'
        res = self.client.put(
            environment_url,
            data={'hierarchy_levels': [None]}
        )
        self.assertEqual(404, res.status_code)
