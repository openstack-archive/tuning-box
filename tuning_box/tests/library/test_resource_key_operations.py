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


class TestResourceDefinitions(BaseTest):

    processor = resource_keys_operation.KeysOperationMixin()

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
