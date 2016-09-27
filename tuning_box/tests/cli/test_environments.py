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


class TestCreateEnvironment(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments',
                      'env create -l lvl1 -i 1 -f json',
                      '{\n  "a": "b"\n}')),
            ('yaml', ('/environments',
                      'env create -l lvl1,lvl2 -i 1  -f yaml',
                      'a: b\n')),
            ('multi', ('/environments',
                       'env create -l lvl1,lvl2 -i 1,2,3  -f yaml',
                       'a: b\n')),
            ('no_data', ('/environments',
                         'env create -f yaml',
                         'a: b\n'))

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


class TestListEnvironments(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments', 'env list -f json', '[]')),
            ('yaml', ('/environments', 'env list -f yaml', '[]\n'))
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


class TestShowEnvironment(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments/9', 'env show 9 -f json -c id',
                      '{\n  "id": 1\n}')),
            ('yaml', ('/environments/9', 'env show 9 -f yaml -c id',
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


class TestDeleteEnvironment(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments/9', 'env delete 9',
                      'Environment with id 9 was deleted\n'))
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


class TestUpdateEnvironment(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('no_data', ('/environments/9', 'env update 9', '{}')),
            ('level', ('/environments/9', 'env update 9 -l lvl1', '{}')),
            ('levels', ('/environments/9',
                        'env update 9 -l lvl1,lvl2',
                        '{}')),
            ('component', ('/environments/9',
                           'env update 9 -l lvl1,lvl2 -i 1',
                           '{}')),
            ('components', ('/environments/9',
                            'env update 9 -l lvl1,lvl2 -i 1,2',
                            '{}')),
            ('erase', ('/environments/9', 'env update 9 -l [] -i 1,2', '{}')),
            ('erase', ('/environments/9', 'env update 9 -l [] -i []', '{}')),
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
