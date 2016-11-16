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

import testscenarios

from tuning_box.tests.cli import _BaseCLITest


class TestHierarchyLevels(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments/9/hierarchy_levels',
                      'lvl list -e 9 -f json', '[]')),
            ('yaml', ('/environments/9/hierarchy_levels',
                      'lvl list -e 9 -f yaml', '[]\n'))
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_get(self):
        self.req_mock.get(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestShowHierarchyLevel(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments/9/hierarchy_levels/n',
                      'lvl show -e 9 -f json -c id n',
                      '{\n  "id": 1\n}')),
            ('yaml', ('/environments/9/hierarchy_levels/nn',
                      'lvl show -e 9 -f yaml -c id nn',
                      'id: 1\n'))
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_get(self):
        self.req_mock.get(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={'id': 1},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())
