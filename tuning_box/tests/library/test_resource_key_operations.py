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
from tuning_box.library import resource_keys_operation
from tuning_box.tests.test_app import BaseTest


class TestResourceKeysOperations(BaseTest):

    processor = resource_keys_operation.KeysOperationMixin()
    object_url = '/environments/{0}/{1}resources/{2}/values'
    object_keys_url = object_url + '/keys/{3}'

    def test_unknown_operation(self):
        self.assertRaises(errors.UnknownKeysOperation,
                          self.processor.perform_operation,
                          'fake_operation', {}, [])

    def test_set_new(self):
        keys = [['a', {}]]
        data = {}
        result = self.processor.do_set(data, keys)
        self.assertEqual({'a': {}}, result)

        keys = [['a', {}], ['a', 'b', []]]
        data = {}
        result = self.processor.do_set(data, keys)
        self.assertEqual({'a': {'b': []}}, result)

        keys = [['a', 0, 'b', 'c_updated']]
        data = {'a': [{'b': 'c'}]}
        result = self.processor.do_set(data, keys)
        self.assertEqual({'a': [{'b': 'c_updated'}]}, result)

        keys = [['a', 'b']]
        data = {'a': {'b': 'c'}}
        result = self.processor.do_set(data, keys)
        self.assertEqual({'a': 'b'}, result)

    def test_set_empty(self):
        keys = [['a', 'b', '']]
        data = {'a': {'b': 'value'}}
        result = self.processor.do_set(data, keys)
        self.assertEqual({'a': {'b': ''}}, result)

    def test_set_not_modifies_storage(self):
        keys = [['a', 'c', 'value_c']]
        data = {'a': {'b': 'value_b'}}
        result = self.processor.do_set(data, keys)
        self.assertEqual({'a': {'b': 'value_b'}}, data)
        self.assertEqual({'a': {'c': 'value_c', 'b': 'value_b'}}, result)

    def test_set_invalid_keys_path(self):
        self.assertRaises(errors.KeysPathInvalid, self.processor.do_set,
                          {}, [[]])
        self.assertRaises(errors.KeysPathInvalid, self.processor.do_set,
                          {}, [['a']])

    def test_set_key_path_not_existed(self):
        keys = [['a', 'b', 'c']]
        data = {}
        self.assertRaises(errors.KeysPathNotExisted, self.processor.do_set,
                          data, keys)

        keys = [['a', 1, 'b']]
        data = {'a': [{'b': 'c'}]}
        self.assertRaises(errors.KeysPathNotExisted, self.processor.do_set,
                          data, keys)

    def test_set_key_path_unreachable(self):
        keys = [['a', 'b', 'c', 'd', 'e']]
        data = {'a': {'b': 'c'}}
        self.assertRaises(errors.KeysPathUnreachable, self.processor.do_set,
                          data, keys)

        keys = [['a', 'k1', 'v1']]
        data = {'a': 'v'}
        self.assertRaises(errors.KeysPathUnreachable, self.processor.do_set,
                          data, keys)

    def test_delete_key_path_not_existed(self):
        keys = [['a', 'b']]
        data = {}
        self.assertRaises(errors.KeysPathNotExisted, self.processor.do_delete,
                          data, keys)

        keys = [[1]]
        data = ['a']
        self.assertRaises(errors.KeysPathNotExisted, self.processor.do_delete,
                          data, keys)

    def test_delete_key_path_unreachable(self):
        keys = [['a', 'b', 'value_b']]
        data = {'a': {'b': 'value_b'}}
        self.assertRaises(errors.KeysPathUnreachable, self.processor.do_delete,
                          data, keys)

        keys = [['a', 'b', 'value_c']]
        data = {'a': {'b': 'value_b'}}
        self.assertRaises(errors.KeysPathUnreachable, self.processor.do_delete,
                          data, keys)

    def test_delete(self):
        keys = [['a']]
        data = {'a': 'val_a', 'b': {'a': 'val_b_a'}}
        result = self.processor.do_delete(data, keys)
        self.assertEqual({'b': {'a': 'val_b_a'}}, result)

        keys = [[0]]
        data = ['a']
        result = self.processor.do_delete(data, keys)
        self.assertEqual([], result)

        keys = [['a', 0, 'b']]
        data = {'a': [{'b': 'val_a_0_b', 'c': 'val_a_0_c'}, 'd']}
        result = self.processor.do_delete(data, keys)
        self.assertEqual({'a': [{'c': 'val_a_0_c'}, 'd']}, result)

        keys = [['a', 'b'], ['a']]
        data = {'a': {'b': 'val_a_b', 'c': 'val_a_c'}, 'b': 'val_b'}
        result = self.processor.do_delete(data, keys)
        self.assertEqual({'b': 'val_b'}, result)

    def test_delete_not_modifies_storage(self):
        keys = [['a', 'b']]
        data = {'a': {'b': 'value_b'}}
        result = self.processor.do_delete(data, keys)
        self.assertEqual({'a': {'b': 'value_b'}}, data)
        self.assertEqual({'a': {}}, result)

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

    def test_put_resource_values_set_consistency(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        environment_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'k0': {'k1': 'v01'}}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        obj_url = self.object_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id
        )
        obj_keys_url = obj_url + '/keys/set'

        # One keys path is invalid
        data = [['kk0', 'v'], ['k0', 'k1', 'k2', 'val']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(409, res.status_code)

        # Checking no changes in the resource value
        res = self.client.get(obj_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual(values, actual)

    def test_put_resource_values_set_nested_keys(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        environment_id = 9
        res_def_id = 5
        levels = (('lvl1', 'val1'), ('lvl2', 'val2'))
        values = {'k0': {'k1': 'v01'}}
        self._add_resource_values(environment_id, res_def_id, levels, values)

        obj_url = self.object_url.format(
            environment_id,
            self.get_levels_path(levels),
            res_def_id
        )
        obj_keys_url = obj_url + '/keys/set'

        data = [['k0', 'k1', 'k2', 'val']]
        res = self.client.put(obj_keys_url, data=data)
        self.assertEqual(409, res.status_code)

        res = self.client.get(obj_url)
        self.assertEqual(200, res.status_code)
        actual = res.json
        self.assertEqual(values, actual)
