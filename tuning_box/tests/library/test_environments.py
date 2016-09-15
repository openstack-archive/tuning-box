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
from tuning_box import library
from tuning_box.library import environments
from tuning_box.tests.test_app import BaseTest


class TestEnvironments(BaseTest):

    collection_url = '/environments'
    object_url = collection_url + '/{0}'

    def test_get_environments_empty(self):
        res = self.client.get(self.collection_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_environments(self):
        self._fixture()
        res = self.client.get(self.collection_url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.json))
        self.assertEqual(
            {'id': 9, 'components': [7], 'hierarchy_levels': ['lvl1', 'lvl2']},
            res.json[0]
        )

    def test_get_one_environment(self):
        self._fixture()
        env_id = 9
        res = self.client.get(self.object_url.format(env_id))
        self.assertEqual(200, res.status_code)
        self.assertEqual(
            {'id': 9, 'components': [7], 'hierarchy_levels': ['lvl1', 'lvl2']},
            res.json
        )

    def test_post_environment_hierarchy_levels_order(self):
        self._fixture()
        levels = ['lvla', 'lvlb']
        data = {'components': [7], 'hierarchy_levels': levels}
        res = self.client.post(self.collection_url, data=data)
        self.assertEqual(201, res.status_code)
        self.assertEqual(levels, res.json['hierarchy_levels'])

    def test_get_one_environment_404(self):
        env_id = 9
        res = self.client.get(self.object_url.format(env_id))
        self.assertEqual(res.status_code, 404)

    def test_post_environment(self):
        self._fixture()
        json = {'components': [7], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = res.json['id']
        self.assertEqual(json, res.json)
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
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(201, res.status_code)
        self.assertEqual(json, res.json)
        self._assert_db_effect(
            db.Environment, 42, environments.environment_fields, json)

    def test_post_environment_preserve_id_conflict(self):
        self._fixture()
        json = {
            'id': 9,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(res.status_code, 409)

    def test_post_environment_preserve_id_conflict_propagate_exc(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        json = {
            'id': 9,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(res.status_code, 409)

    def test_post_environment_by_component_name(self):
        self._fixture()
        json = {
            'components': ['component1'],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = res.json['id']
        json['components'] = [7]
        self.assertEqual(json, res.json)
        self._assert_db_effect(
            db.Environment, res.json['id'],
            environments.environment_fields, json)

    def test_post_components_duplication(self):
        self._fixture()
        json = {
            'components': ['component1', 7],
            'hierarchy_levels': ['lvl'],
        }
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(409, res.status_code)

    def test_post_components_no_duplication(self):
        self._fixture()
        components_url = '/components'
        res = self.client.get(components_url)
        self.assertEqual(200, res.status_code)
        component = res.json[0]

        # Creating component with name equal to id of existed component
        res = self.client.post(
            components_url,
            data={
                'name': component['id'],
                'resource_definitions': []
            }
        )
        self.assertEqual(201, res.status_code)
        new_component = res.json

        # Checking no components duplication detected
        json = {
            'components': [component['id'], new_component['name']],
            'hierarchy_levels': ['lvl'],
        }
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(201, res.status_code)

    def test_post_environment_404(self):
        self._fixture()
        json = {'components': [8], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(res.status_code, 404)
        self._assert_not_in_db(db.Environment, 10)

    def test_post_environment_by_component_name_404(self):
        self._fixture()
        json = {
            'components': ['component2'],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post(self.collection_url, data=json)
        self.assertEqual(res.status_code, 404)
        self._assert_not_in_db(db.Environment, 10)

    def test_delete_environment(self):
        self._fixture()
        env_id = 9
        env_url = self.object_url.format(env_id)
        res = self.client.get(env_url)
        self.assertEqual(200, res.status_code)
        levels = ['lvl1', 'lvl2']
        self.assertEqual(levels, res.json['hierarchy_levels'])

        res = self.client.delete(env_url)
        self.assertEqual(204, res.status_code)
        self.assertEqual(res.data, b'')
        self._assert_not_in_db(db.Environment, 9)

        with self.app.app_context():
            for name in levels:
                obj = db.EnvironmentHierarchyLevel.query.filter(
                    db.EnvironmentHierarchyLevel.name == name
                ).first()
                self.assertIsNone(obj)

    def test_delete_environment_404(self):
        env_id = 9
        res = self.client.delete(self.object_url.format(env_id))
        self.assertEqual(res.status_code, 404)

    def test_put_environment_404(self):
        env_id = 7
        res = self.client.put(self.object_url.format(env_id))
        self.assertEqual(res.status_code, 404)

    def test_put_environment_components(self):
        self._fixture()
        environment_url = '/environments/9'
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
        self.assertEqual(initial, actual)

    def test_put_environment_component_not_found(self):
        self._fixture()
        env_id = 9
        res = self.client.put(
            self.object_url.format(env_id),
            data={'components': [None]}
        )
        self.assertEqual(404, res.status_code)

    def check_hierarchy_levels(self, hierarchy_levels_names):
        with self.app.app_context():
            hierarchy_levels = library.load_objects_by_id_or_name(
                db.EnvironmentHierarchyLevel, hierarchy_levels_names)
            parent_id = None
            for level in hierarchy_levels:
                self.assertEqual(parent_id, level.parent_id)
                parent_id = level.id

    def test_put_environment_hierarchy_levels(self):
        self._fixture()
        env_id = 9
        environment_url = self.object_url.format(env_id)
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
        self.assertEqual(initial, actual)
        self.check_hierarchy_levels(actual['hierarchy_levels'])

    def test_put_environment_hierarchy_levels_remove_level(self):
        self._fixture()
        env_id = 9
        environment_url = self.object_url.format(env_id)
        initial = self.client.get(environment_url).json
        expected_levels = initial['hierarchy_levels'][1:]

        # Updating hierarchy levels
        res = self.client.put(
            environment_url,
            data={'hierarchy_levels': expected_levels}
        )
        self.assertEqual(204, res.status_code)
        actual = self.client.get(environment_url).json
        self.assertEqual(expected_levels, actual['hierarchy_levels'])
        self.check_hierarchy_levels(actual['hierarchy_levels'])

    def test_put_environment_hierarchy_levels_reverse(self):
        self._fixture()
        env_id = 9
        env_url = self.object_url.format(env_id)
        initial = self.client.get(env_url).json
        expected_levels = initial['hierarchy_levels']
        expected_levels.reverse()

        # Updating hierarchy levels
        res = self.client.put(
            env_url,
            data={'hierarchy_levels': expected_levels}
        )
        self.assertEqual(204, res.status_code)
        actual = self.client.get(env_url).json
        self.assertEqual(expected_levels, actual['hierarchy_levels'])
        self.check_hierarchy_levels(actual['hierarchy_levels'])

    def test_put_environment_hierarchy_levels_with_new_level(self):
        self._fixture()
        env_id = 9
        env_url = self.object_url.format(env_id)
        initial = self.client.get(env_url).json
        expected_levels = ['root'] + initial['hierarchy_levels']

        res = self.client.put(
            env_url,
            data={'hierarchy_levels': expected_levels}
        )
        self.assertEqual(204, res.status_code)

        res = self.client.get('/environments/9/hierarchy_levels')
        self.assertEqual(200, res.status_code)

        res = self.client.get(env_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual(expected_levels, actual['hierarchy_levels'])
        self.check_hierarchy_levels(actual['hierarchy_levels'])
