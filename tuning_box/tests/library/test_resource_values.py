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

import itertools
import uuid

import six

from tuning_box import db
from tuning_box.tests.test_app import BaseTest


class TestResourceValues(BaseTest):

    object_url = '/environments/{0}/{1}resources/{2}/values'
    object_keys_url = object_url + '/keys/{3}'

    def get_levels_path(self, levels):
        if levels:
            return '/'.join(itertools.chain.from_iterable(levels)) + '/'
        else:
            return ''

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
            level = level_value.level.parent
            self.assertIsNotNone(level)
            self.assertEqual(level.name, 'lvl1')
            self.assertIsNone(level.parent)

    def test_put_resource_values_bad_level(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        res = self.client.put('/environments/9/lvlx/1/resources/5/values',
                              data={'k': 'v'})
        self.assertEqual(res.status_code, 404)
        self.assertEqual(
            {"msg": "Unexpected level name 'lvlx'. Expected 'lvl1'."},
            res.json
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

    def test_get_resource_values_by_name(self):
        self._fixture()
        env_id = 9
        res_name = 'resdef1'
        object_url = self.object_url.format(
            env_id, '', res_name
        )
        res = self.client.get(object_url)
        self.assertEqual(200, res.status_code)
        self.assertEqual({}, res.json)

    def test_get_resource_values_effective(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        self.assertEqual(204, res.status_code)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values?effective',
        )
        self.assertEqual(200, res.status_code)
        self.assertEqual(res.json, {'key': 'value'})

    def test_get_resource_values_redirect_by_name_with_query(self):
        self._fixture()
        env_id = 9
        res_name = 'resdef1'
        obj_url = self.object_url.format(env_id, '', res_name)
        expected = {'key': 'value'}
        self.client.put(obj_url, data=expected)
        res = self.client.get(obj_url + '?effective')
        self.assertEqual(200, res.status_code)
        self.assertEqual(expected, res.json)

    def test_put_resource_values_by_name(self):
        self._fixture()
        env_id = 9
        res_name = 'resdef1'
        obj_url = self.object_url.format(
            env_id, '', res_name
        )
        expected = {'key': 'value'}
        res = self.client.put(obj_url, data=expected)
        self.assertEqual(res.status_code, 204)
        res = self.client.get(obj_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(expected, res.json)

    def test_put_resource_values_not_found(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()

        res = self.client.put(
            '/environments/9/lvl1/val1/resources/5/values/keys/set',
            data={}
        )
        self.assertEqual(404, res.status_code)

    def test_put_resource_values_set_operation_error(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()

        environment_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'key': 'val'}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        data = [['a', 'b', 'c', 'value']]
        obj_keys_url = self.object_keys_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id,
            'set'
        )

        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(409, res.status_code)

    def test_put_resource_values_set(self):
        self._fixture()
        environment_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'key': 'val'}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        obj_url = self.object_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id
        )
        obj_keys_url = obj_url + '/keys/set'

        data = [['key', 'key_value'], ['key_x', 'key_x_value']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(204, res.status_code)

        res = self.client.get(obj_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual({'key': 'key_value', 'key_x': 'key_x_value'},
                         actual)

    def test_put_resource_values_levels_mismatch(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        env_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'), ('lvl3', 'val3'))
        values = {'key': 'val'}

        res = self._add_resource_values(
            env_id, res_def_id, levels, values, expect_code=404)
        self.assertEqual(
            {'msg': "Levels [u'lvl1', u'lvl2', u'lvl3'] can't be matched with "
                    "environment 9 levels: [u'lvl1', u'lvl2']"},
            res.json
        )

    def test_put_resource_values_levels_mismatch_for_empty_levels(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        env_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'), ('lvl3', 'val3'))
        values = {'key': 'val'}

        env_url = '/environments/{0}'.format(env_id)
        res = self.client.put(env_url, data={'hierarchy_levels': []})
        self.assertEqual(204, res.status_code)

        res = self.client.get(env_url)
        self.assertEqual(200, res.status_code)
        self.assertEqual([], res.json['hierarchy_levels'])

        res = self._add_resource_values(
            env_id, res_def_id, levels, values, expect_code=404)
        self.assertEqual(
            {'msg': "Levels [u'lvl1', u'lvl2', u'lvl3'] can't be matched with "
                    "environment 9 levels: []"},
            res.json
        )

    def test_put_resource_values_set_no_levels(self):
        self._fixture()
        environment_id = 9
        res_def_id = 5
        values = {'key': 'val'}
        self._add_resource_values(environment_id, res_def_id, (), values)

        obj_url = '/environments/{0}/resources/{1}/values'.format(
            environment_id, res_def_id)
        obj_keys_url = obj_url + '/keys/set'

        data = [['key', 'key_value'], ['key_x', 'key_x_value']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(204, res.status_code)

        res = self.client.get(obj_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual({'key': 'key_value', 'key_x': 'key_x_value'},
                         actual)

    def test_put_resource_values_delete(self):
        self._fixture()
        environment_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'key_0': 'val_0', 'key_1': 'val_1'}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        obj_url = self.object_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id
        )
        obj_keys_url = obj_url + '/keys/delete'

        data = [['key_0']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(204, res.status_code)

        res = self.client.get(obj_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual({'key_1': 'val_1'}, actual)

    def test_put_resource_values_delete_by_name(self):
        self._fixture()
        environment_id = 9
        res_def_id = 5
        res_def_name = 'resdef1'
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'key_0': 'val_0', 'key_1': 'val_1'}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        obj_url = self.object_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_name
        )
        obj_keys_url = obj_url + '/keys/delete'

        data = [['key_0']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(204, res.status_code)

        obj_url = self.object_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id
        )

        res = self.client.get(obj_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual({'key_1': 'val_1'}, actual)

    def test_put_resource_values_delete_operation_error(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        environment_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'key_0': 'val_0', 'key_1': 'val_1'}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        obj_keys_url = self.object_keys_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id,
            'delete'
        )
        data = [['fake_key']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(409, res.status_code)

        data = [['key_0', 'val_0']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(409, res.status_code)

    def test_get_resource_values_effective_with_lookup(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key0': 'root_value_0',
                                    'key1': 'root_value_1',
                                    'key2': 'root_value_2',
                                    'key3': 'root_value_3'})
        self.assertEqual(res.status_code, 204)

        # Set key0 value on level1
        res = self.client.put('/environments/9/lvl1/1/resources/5/values',
                              data={'key0': 'lvl1_value_0'})
        self.assertEqual(res.status_code, 204)

        # Set key1, key2 values on level1/level2
        res = self.client.put(
            '/environments/9/lvl1/1/lvl2/2/resources/5/values',
            data={'key1': 'lvl2_value_1', 'key2': 'lvl2_value_2'}
        )
        self.assertEqual(res.status_code, 204)

        # Checking lookup info
        res = self.client.get(
            '/environments/9/lvl1/1/lvl2/2/resources/5/values?'
            'effective&show_lookup',
        )
        self.assertEqual(res.status_code, 200)
        expected = {
            'key0': ['lvl1_value_0', '/lvl1/1/'],
            'key1': ['lvl2_value_1', '/lvl1/1/lvl2/2/'],
            'key2': ['lvl2_value_2', '/lvl1/1/lvl2/2/'],
            'key3': ['root_value_3', '/']
        }
        self.assertEqual(expected, res.json)

    def generate_values(self, size):
        result = {}
        for i in six.moves.range(size):
            result[six.text_type(uuid.uuid4())] = i
        return result

    def test_get_resource_values_effective_lot_of_data(self):
        self._fixture()
        env_id = 9
        res_id = 5
        keys_on_root = 10000
        keys_on_lvl1 = 15000
        keys_on_lvl2 = 20000
        values_on_level = 500

        # Adding values on the root level
        self._add_resource_values(
            env_id, res_id, (), self.generate_values(keys_on_root))

        # Adding values on the level lvl1 and lvl2
        lvl_1_values = self.generate_values(keys_on_lvl1)
        lvl_2_values = self.generate_values(keys_on_lvl2)
        for lvl_val in six.moves.range(values_on_level):
            lvl_val = six.text_type(lvl_val)
            self._add_resource_values(
                env_id, res_id, (('lvl1', lvl_val),), lvl_1_values)
            self._add_resource_values(
                env_id, res_id, (('lvl1', lvl_val), ('lvl2', lvl_val)),
                lvl_2_values)

        with self.app.app_context():
            res_vals_count = db.ResourceValues.query.count()
            self.assertEqual(1 + values_on_level * 2, res_vals_count)

        # Check keys num on root level
        obj_url = self.object_url.format(
            env_id, self.get_levels_path(()),
            res_id
        )
        res = self.client.get(obj_url)
        self.assertEqual(keys_on_root, len(res.json))

        res = self.client.get(obj_url + '?effective')
        self.assertEqual(keys_on_root, len(res.json))

        # Check keys num on lvl1
        obj_url = self.object_url.format(
            env_id, self.get_levels_path((('lvl1', '1'),)),
            res_id
        )
        res = self.client.get(obj_url)
        self.assertEqual(keys_on_lvl1, len(res.json))

        res = self.client.get(obj_url + '?effective')
        self.assertEqual(keys_on_root + keys_on_lvl1, len(res.json))

        # Check keys num on lvl2
        obj_url = self.object_url.format(
            env_id, self.get_levels_path((('lvl1', '1'), ('lvl2', '2'))),
            res_id
        )
        res = self.client.get(obj_url)
        self.assertEqual(keys_on_lvl2, len(res.json))

        res = self.client.get(obj_url + '?effective')
        self.assertEqual(keys_on_root + keys_on_lvl1 + keys_on_lvl2,
                         len(res.json))
