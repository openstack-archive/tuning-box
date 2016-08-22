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
                      'env create --levels lvl1 --components 1 --format json',
                      '{}')),
            ('yaml', ('/environments',
                      'env create --levels lvl1,lvl2 --components 1  '
                      '--format yaml',
                      '{}\n')),
            ('plain', ('/environments',
                       'env create --levels lvl1,lvl2 --components 1,2,3  '
                       '--format plain',
                       '{}')),
            ('plain', ('/environments',
                       'env create '
                       '--format plain',
                       '{}'))
        ]
    ]

    mock_url = None
    args = None
    expected_result = None

    def test_post(self):
        self.req_mock.post(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestListEnvironments(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments', 'env list', '{}')),
            ('yaml', ('/environments', 'env list --format yaml', '{}\n')),
            ('plain', ('/environments', 'env list --format plain', '{}'))
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
            ('json', ('/environments/9', 'env show 9 --format json', '{}')),
            ('yaml', ('/environments/9', 'env show 9 --format yaml', '{}\n')),
            ('plain', ('/environments/9', 'env show 9 --format plain', '{}'))
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


class TestDeleteEnvironment(testscenarios.WithScenarios, _BaseCLITest):

    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('json', ('/environments/9', 'env delete 9 --format json',
                      '{}')),
            ('yaml', ('/environments/9', 'env delete 9 --format yaml',
                      '{}\n')),
            ('plain', ('/environments/9', 'env delete 9 --format plain',
                       '{}'))
        ]
    ]
    mock_url = None
    args = None
    expected_result = None

    def test_delete(self):
        self.req_mock.delete(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={}
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())
