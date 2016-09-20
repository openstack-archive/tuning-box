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

import six

from tuning_box import db
from tuning_box import errors
from tuning_box.library import hierarchy_levels
from tuning_box.tests.test_app import BaseTest


class TestLevelsHierarchy(BaseTest):

    collection_url = '/environments/{0}/hierarchy_levels'
    object_url = collection_url + '/{1}'

    def test_get_environment_level_value_root(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = hierarchy_levels.get_environment_level_value(
                db.Environment(id=9),
                [],
            )
            self.assertIsNone(level_value)

    def test_get_environment_level_value_deep(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = hierarchy_levels.get_environment_level_value(
                db.Environment(id=9),
                [('lvl1', 'val1'), ('lvl2', 'val2')],
            )
            self.assertIsNotNone(level_value)
            self.assertEqual(level_value.level.name, 'lvl2')
            self.assertEqual(level_value.value, 'val2')
            level = level_value.level.parent
            self.assertIsNotNone(level)
            self.assertEqual(level.name, 'lvl1')
            self.assertIsNone(level.parent)

    def test_get_environment_level_value_bad_level(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            exc = self.assertRaises(
                errors.TuningboxNotFound,
                hierarchy_levels.get_environment_level_value,
                db.Environment(id=9),
                [('lvlx', 'val1')],
            )
            self.assertEqual(
                six.text_type(exc),
                "Unexpected level name 'lvlx'. Expected 'lvl1'.",
            )

    def test_get_hierarchy_levels(self):
        self._fixture()
        environment_id = 9
        expected_levels = ['lvl1', 'lvl2']
        res = self.client.get(self.collection_url.format(environment_id))
        self.assertEqual(200, res.status_code)
        self.assertEqual(expected_levels, [d['name'] for d in res.json])

    def test_get_hierarchy_levels_not_found(self):
        environment_id = 9
        res = self.client.get(self.collection_url.format(environment_id))
        self.assertEqual(404, res.status_code)

    def test_get_hierarchy_level(self):
        self._fixture()
        environment_id = 9
        levels = ['lvl1', 'lvl2']
        for level in levels:
            res = self.client.get(self.object_url.format(environment_id,
                                                         level))
            self.assertEqual(200, res.status_code)
            self.assertEqual(level, res.json['name'])

    def test_get_hierarchy_level_not_found(self):
        levels = ['lvl1', 'lvl2']
        for level in levels:
            res = self.client.get(self.object_url.format(9, level))
            self.assertEqual(404, res.status_code)

    def test_put_hierarchy_level(self):
        self._fixture()
        environment_id = 9
        level = 'lvl1'
        new_name = 'new_{0}'.format(level)
        res = self.client.put(self.object_url.format(environment_id, level),
                              data={'name': new_name})
        self.assertEqual(204, res.status_code)

        res = self.client.get(self.object_url.format(environment_id, new_name))
        self.assertEqual(200, res.status_code)
        self.assertEqual(new_name, res.json['name'])

    def test_put_hierarchy_level_not_found(self):
        self._fixture()
        environment_id = 9
        res = self.client.put(self.object_url.format(environment_id, 'xx'),
                              data={'name': 'new_name'})
        self.assertEqual(404, res.status_code)

        res = self.client.put(self.object_url.format(1, 'lvl1'),
                              data={'name': 'new_name'})
        self.assertEqual(404, res.status_code)

        res = self.client.put(self.object_url.format(1, 'xx'),
                              data={'name': 'new_name'})
        self.assertEqual(404, res.status_code)
