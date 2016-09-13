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
import yaml

from tuning_box.tests.cli import _BaseCLITest


class TestCreateResourceDefinition(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0],
         dict(zip(('args', 'expected_body', 'stdin'), s[1])))
        for s in [
            ('json', ('def create -n n -i 1 -d json -f yaml',
                      'content: {}\ncomponent_id: 1\nid: 1\nname: n\n',
                      '{"a": 3}')),
            ('yaml', ('def create -n n -i 1 -d yaml -f yaml',
                      'content: {}\ncomponent_id: 1\nid: 1\nname: n\n',
                      'a: b\n')),
        ]
    ]

    args = None
    expected_body = None
    stdin = None

    def test_post(self):
        url = self.BASE_URL + '/resource_definitions'
        self.req_mock.post(
            url,
            headers={'Content-Type': 'application/json'},
            json={'id': 1, 'component_id': 1, 'name': 'n', 'content': {}}
        )
        if self.stdin:
            self.cli.stdin.write(self.stdin)
            self.cli.stdin.seek(0)
        self.cli.run(self.args.split())
        self.assertEqual(
            yaml.safe_load(self.expected_body),
            yaml.safe_load(self.cli.stdout.getvalue())
        )


class TestListResourceDefinitions(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/resource_definitions', 'def list -f json', '[]')),
            ('yaml', ('/resource_definitions', 'def list --format yaml',
                      '[]\n')),
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
            ('yaml', ('/resource_definitions/9', 'def show 9 -f yaml',
                      'id: 1\nname: n\ncomponent_id: 2\ncontent: {}\n')),
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_get(self):
        self.req_mock.get(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={'id': 1, 'name': 'n', 'component_id': 2, 'content': {}},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestDeleteComponent(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('', ('/resource_definitions/9', 'def delete 9',
                  'Resource_definition with id 9 was deleted')),
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


class TestUpdateResourceDefinition(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('args', 'expected_result', 'stdin'), s[1])))
        for s in [
            ('no_data', ('def update 9', '{}')),
            ('name', ('def update 9 -n comp_name', '{}', False)),
            ('component_id', ('def update 9 -i 1', '{}', False)),
            ('content', ('def update 9 -p "a" -t yaml', '{}', False)),
            ('stdin_content', ('def update 9 -d yaml', '{}', 'a: b')),
            ('stdin_content', ('def update 9 -d yaml', '{}', 'a: b')),
        ]
    ]
    args = None
    expected_result = None
    stdin = None

    def test_update(self):
        self.req_mock.patch(
            self.BASE_URL + '/resource_definitions/9',
            headers={'Content-Type': 'application/json'},
            json={}
        )
        if self.stdin:
            self.cli.stdin.write(self.stdin)
            self.cli.stdin.seek(0)
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())
