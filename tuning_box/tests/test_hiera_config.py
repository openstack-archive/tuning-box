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

import mock

from tuning_box import hiera_config
from tuning_box.tests import base


class TestHieraConfig(base.TestCase):

    def test_load_config(self):
        data = '!ruby/sym r_key: r_val\n'
        with mock.patch('__builtin__.open', mock.mock_open(read_data=data)):
            result = hiera_config.load_config()
            self.assertEqual({'r_key': 'r_val'}, result)
