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
from tuning_box.library import resource_key_operations
from tuning_box.tests.test_app import BaseTest


class TestResourceDefinitions(BaseTest):

    processor = resource_key_operations.KeysOperationsMixin()

    def test_unknown_operation(self):
        self.assertRaises(errors.UnknownKeysOperation,
                          self.processor.perform_operation,
                          'fake_operation', {}, [])

    def test_set_new(self):
        keys = [['a', {}]]
        data = {}
        self.processor.do_set(data, keys)
        self.assertEqual({'a': {}}, data)

        keys = [['a', {}], ['a', 'b', []]]
        data = {}
        self.processor.do_set(data, keys)
        self.assertEqual({'a': {'b': []}}, data)

        keys = [['a', 0, 'b', 'c_updated']]
        data = {'a': [{'b': 'c'}]}
        self.processor.do_set(data, keys)
        self.assertEqual({'a': [{'b': 'c_updated'}]}, data)

        keys = [['a', 'b']]
        data = {'a': {'b': 'c'}}
        self.processor.do_set(data, keys)
        self.assertEqual({'a': 'b'}, data)

    def test_set_empty(self):
        keys = [['a', 'b', '']]
        data = {'a': {'b': 'value'}}
        self.processor.do_set(data, keys)
        self.assertEqual({'a': {'b': ''}}, data)

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
