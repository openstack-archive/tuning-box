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


class TestCreateComponent(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/components',
                      'comp create --name comp_name --format json',
                      '{\n  "a": "b"\n}')),
            ('yaml', ('/components',
                      'comp create -n comp_name -f yaml',
                      'a: b\n')),
        ]
    ]

    mock_url = None
    args = None
    expected_result = None

    def test_post(self):
        self.req_mock.post(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={'a': 'b'},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestListComponents(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/components', 'comp list -f json', '[]')),
            ('yaml', ('/components', 'comp list --format yaml', '[]\n')),
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_get(self):
        self.req_mock.get(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json=[],
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestShowComponent(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('yaml', ('/components/9', 'comp show 9 -f yaml',
                      'id: 1\nname: n\nresource_definitions: []\n')),
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_get(self):
        self.req_mock.get(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={'id': 1, 'name': 'n', 'resource_definitions': []},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestDeleteComponent(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('', ('/components/9', 'comp delete 9',
                  'Component with id 9 was deleted\n')),
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_delete(self):
        self.req_mock.delete(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'}
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestUpdateComponent(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('no_data', ('/components/9', 'comp update 9', '{}')),
            ('s_name', ('/components/9',
                        'comp update 9 -n comp_name', '{}')),
            ('l_name', ('/components/9',
                        'comp update 9 --name comp_name', '{}')),
            ('s_r_defs', ('/components/9',
                          'comp update 9 -r 1,2 ', '{}')),
            ('l_r_ders', ('/components/9',
                          'comp update 9 --resource-definitions 1,2', '{}')),
            ('empty_s_r_defs', ('/components/9',
                                'comp update 9 -r [] -n comp_name', '{}')),
            ('empty_l_r_defs', ('/components/9',
                                'comp update 9 --resource-definitions []',
                                '{}'))
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_update(self):
        self.req_mock.patch(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={}
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())
