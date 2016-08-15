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
from tuning_box.tests.test_app import BaseTest


class TestResourceValues(BaseTest):

    def test_put_resource_values_root(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'k': 'v'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNotNone(resource_values)
            self.assertEqual(resource_values.values, {'k': 'v'})
            self.assertIsNone(resource_values.level_value)

    def test_put_resource_values_deep(self):
        self._fixture()
        res = self.client.put(
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values',
            data={'k': 'v'},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNotNone(resource_values)
            self.assertEqual(resource_values.values, {'k': 'v'})
            level_value = resource_values.level_value
            self.assertEqual(level_value.level.name, 'lvl2')
            self.assertEqual(level_value.value, 'val2')
            level_value = level_value.parent
            self.assertEqual(level_value.level.name, 'lvl1')
            self.assertEqual(level_value.value, 'val1')
            self.assertIsNone(level_value.parent)

    def test_put_resource_values_bad_level(self):
        self._fixture()
        res = self.client.put('/environments/9/lvlx/1/resources/5/values',
                              data={'k': 'v'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json,
            {"message": "Unexpected level name 'lvlx'. Expected 'lvl1'."},
        )
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNone(resource_values)

    def test_get_resource_values(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {})

    def test_get_resource_values_effective(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values?effective',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'key': 'value'})

    def test_get_resource_values_redirect(self):
        self._fixture()
        self.client.put('/environments/9/resources/5/values',
                        data={'key': 'value'})
        res = self.client.get(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/values',
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values',
        )

    def test_get_resource_values_redirect_with_query(self):
        self._fixture()
        self.client.put('/environments/9/resources/5/values',
                        data={'key': 'value'})
        res = self.client.get(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/values'
            '?effective',
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values?effective',
        )

    def test_put_resource_values_redirect(self):
        self._fixture()
        res = self.client.put(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/values',
            data={'k': 'v'},
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values',
        )
