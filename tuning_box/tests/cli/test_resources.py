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

from tuning_box.cli import base as cli_base
from tuning_box.tests import base
from tuning_box.tests.cli import _BaseCLITest


class TestLevelsConverter(testscenarios.WithScenarios, base.TestCase):
    scenarios = [
        (s[0], dict(zip(('input', 'expected_result', 'expected_error'), s[1])))
        for s in [
            ('empty', ('', None, TypeError)),
            ('one', ('lvl=val', [('lvl', 'val')])),
            ('two', ('lvl1=val1,lvl2=val2', [('lvl1', 'val1'),
                                             ('lvl2', 'val2')])),
            ('no_eq', ('val', None, TypeError)),
            ('no_eq2', ('lvl1=val2,val', None, TypeError)),
            ('two_eq', ('lvl1=foo=baz', [('lvl1', 'foo=baz')])),
        ]
    ]

    input = None
    expected_result = None
    expected_error = None

    def test_levels(self):
        if self.expected_error:
            self.assertRaises(
                self.expected_error, cli_base.level_converter, self.input)
        else:
            res = cli_base.level_converter(self.input)
            self.assertEqual(self.expected_result, res)


class TestGet(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('global,json', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --format=json',
                '{\n  "hello": "world"\n}',
            )),
            ('lowlevel,json', (
                '/environments/1/lvl1/value1/resources/1/values?effective',
                'get --env 1 --level lvl1=value1 --resource 1  --format=json',
                '{\n  "hello": "world"\n}',
            )),
            ('global,yaml', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --format yaml',
                'hello: world\n',
            )),
            ('lowlevel,yaml', (
                '/environments/1/lvl1/value1/resources/1/values?effective',
                'get --env 1 --level lvl1=value1 --resource 1 --format yaml',
                'hello: world\n',
            )),
            ('key,json', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key hello --format json',
                '{\n  "hello": "world"\n}',
            )),
            ('key,yaml', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key hello --format yaml',
                'hello: world\n',
            )),
            ('no_key,json', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key no --format json',
                '{\n  "no": {}\n}',
            )),
            ('no_key,yaml', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key no --format yaml',
                "'no': {}\n",
            ))
        ]
    ]

    mock_url = None
    args = None
    expected_result = None

    def test_get(self):
        self.req_mock.get(
            self.BASE_URL + self.mock_url,
            headers={'Content-Type': 'application/json'},
            json={'hello': 'world'},
        )
        self.cli.run(self.args.split())
        self.assertEqual(self.expected_result, self.cli.stdout.getvalue())


class TestSet(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0],
         dict(zip(('args', 'expected_body', 'should_get', 'stdin'), s[1])))
        for s in [
            ('json', ('--format json', {'a': 3}, False, '{"a": 3}')),
            ('yaml', ('--format yaml', {'a': 3}, False, 'a: 3')),
            ('key,json', ('--key b --format json', {'a': 1, 'b': {'a': 3}},
                          True, '{"a": 3}')),
            ('key,yaml', ('--key b --format yaml', {'a': 1, 'b': {'a': 3}},
                          True, 'a: 3')),
            ('key,null', ('--key b --type null', {'a': 1, 'b': None})),
            ('key,str', ('--key b --type str --value 4', {'a': 1, 'b': '4'})),
        ]
    ]

    args = None
    expected_body = None
    should_get = True
    stdin = None

    url_last_part = 'values'
    cmd = 'set'

    def test_set(self):
        url = self.BASE_URL + '/environments/1/lvl1/value1/resources/1/' + \
            self.url_last_part
        self.req_mock.put(url)
        if self.should_get:
            self.req_mock.get(
                url,
                headers={'Content-Type': 'application/json'},
                json={'a': 1, 'b': True},
            )
        args = [self.cmd] + ("--env 1 --level lvl1=value1 --resource 1 " +
                             self.args).split()
        if self.stdin:
            self.cli.stdin.write(self.stdin)
            self.cli.stdin.seek(0)
        self.cli.run(args)
        req_history = self.req_mock.request_history
        if self.should_get:
            self.assertEqual('GET', req_history[0].method)
        self.assertEqual('PUT', req_history[-1].method)
        self.assertEqual(self.expected_body, req_history[-1].json())


class TestDelete(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0],
         dict(zip(('args', 'expected_body'), s[1])))
        for s in [
            ('k1', ('-k k1', "ResourceValue for key k1 was deleted\n")),
            ('xx', ('-k xx', "ResourceValue for key xx was deleted\n")),
        ]
    ]

    args = None
    expected_body = None
    url_last_part = 'values'
    cmd = 'del'

    def test_delete(self):
        url = self.BASE_URL + '/environments/1/lvl1/value1/resources/1/' + \
            self.url_last_part + '/keys/delete'
        self.req_mock.patch(url)
        args = [self.cmd] + ("--env 1 --level lvl1=value1 --resource 1 " +
                             self.args).split()
        self.cli.run(args)
        self.assertEqual(self.expected_body, self.cli.stdout.getvalue())


class TestOverride(TestSet):
    url_last_part = 'overrides'
    cmd = 'override'


class TestDeleteOverride(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0],
         dict(zip(('args', 'expected_body'), s[1])))
        for s in [
            ('k1', ('-k k1', "ResourceOverride for key k1 was deleted\n")),
            ('xx', ('-k xx', "ResourceOverride for key xx was deleted\n")),
        ]
    ]

    args = None
    expected_body = None
    url_last_part = 'overrides'
    cmd = 'del override'

    def test_delete(self):
        url = self.BASE_URL + '/environments/1/lvl1/value1/resources/1/' + \
            self.url_last_part + '/keys/delete'
        self.req_mock.patch(url)
        args = [self.cmd] + ("--env 1 --level lvl1=value1 --resource 1 " +
                             self.args).split()
        self.cli.run(args)
        self.assertEqual(self.expected_body, self.cli.stdout.getvalue())
