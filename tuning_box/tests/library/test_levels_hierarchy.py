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

import werkzeug

from tuning_box import db
from tuning_box.library import levels_hierarchy
from tuning_box.tests.test_app import BaseTest


class TestLevelsHierarchy(BaseTest):

    def test_get_environment_level_value_root(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = levels_hierarchy.get_environment_level_value(
                db.Environment(id=9),
                [],
            )
            self.assertIsNone(level_value)

    def test_get_environment_level_value_deep(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = levels_hierarchy.get_environment_level_value(
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
                werkzeug.exceptions.BadRequest,
                levels_hierarchy.get_environment_level_value,
                db.Environment(id=9),
                [('lvlx', 'val1')],
            )
            self.assertEqual(
                exc.description,
                "Unexpected level name 'lvlx'. Expected 'lvl1'.",
            )
