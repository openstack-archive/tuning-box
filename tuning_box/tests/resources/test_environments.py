#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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

from werkzeug import exceptions

from tuning_box import db
from tuning_box.resources import environments
from tuning_box.tests.test_app import TestApp


class TestEnvironments(TestApp):

    def test_get_environments_empty(self):
        res = self.client.get('/environments')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_environments(self):
        self._fixture()
        res = self.client.get('/environments')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [{'id': 9, 'components': [7],
                                     'hierarchy_levels': ['lvl1', 'lvl2']}])

    def test_get_one_environment(self):
        self._fixture()
        res = self.client.get('/environments/9')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'id': 9, 'components': [7],
                                    'hierarchy_levels': ['lvl1', 'lvl2']})

    def test_get_one_environment_404(self):
        res = self.client.get('/environments/9')
        self.assertEqual(res.status_code, 404)

    def test_post_environment(self):
        self._fixture()
        json = {'components': [7], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = 10
        self.assertEqual(res.json, json)
        self._assert_db_effect(
            db.Environment, 10, environments.environment_fields, json)

    def test_post_environment_preserve_id(self):
        self._fixture()
        json = {
            'id': 42,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json, json)
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
        json['id'] = 10
        json['components'] = [7]
        self.assertEqual(res.json, json)
        self._assert_db_effect(
            db.Environment, 10, environments.environment_fields, json)

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

    def test_get_environment_level_value_root(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = environments.get_environment_level_value(
                db.Environment(id=9),
                [],
            )
            self.assertIsNone(level_value)

    def test_get_environment_level_value_deep(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = environments.get_environment_level_value(
                db.Environment(id=9),
                [('lvl1', 'val1'), ('lvl2', 'val2')],
            )
            self.assertIsNotNone(level_value)
            self.assertEqual(level_value.level.name, 'lvl2')
            self.assertEqual(level_value.value, 'val2')
            level_value = level_value.parent
            self.assertEqual(level_value.level.name, 'lvl1')
            self.assertEqual(level_value.value, 'val1')
            self.assertIsNone(level_value.parent)

    def test_get_environment_level_value_bad_level(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            exc = self.assertRaises(
                exceptions.BadRequest,
                environments.get_environment_level_value,
                db.Environment(id=9),
                [('lvlx', 'val1')],
            )
            self.assertEqual(
                exc.description,
                "Unexpected level name 'lvlx'. Expected 'lvl1'.",
            )
