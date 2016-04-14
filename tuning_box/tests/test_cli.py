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

import io

from requests_mock.contrib import fixture as req_fixture
import testscenarios

from tuning_box import cli
from tuning_box.cli import base as cli_base
from tuning_box import client as tb_client
from tuning_box.tests import base


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


class FormatOutputTest(testscenarios.WithScenarios, base.TestCase):
    scenarios = [
        (s[0], dict(zip(('output', 'format_', 'expected_result'), s[1])))
        for s in [
            ('none,plain', (None, 'plain', '')),
            ('none,json', (None, 'json', 'null')),
            # TODO(yorik-sar): look into why YAML return those elipsis
            ('none,yaml', (None, 'yaml', 'null\n...\n')),
            ('str,plain', (u"a string", 'plain', 'a string')),
            ('str,json', (u"a string", 'json', '"a string"')),
            ('str,yaml', (u"a string", 'yaml', 'a string\n...\n')),
            ('int,plain', (42, 'plain', '42')),
            ('int,json', (42, 'json', '42')),
            ('int,yaml', (42, 'yaml', '42\n...\n')),
            ('float,plain', (1.2, 'plain', '1.2')),
            ('float,json', (1.2, 'json', '1.2')),
            ('float,yaml', (1.2, 'yaml', '1.2\n...\n')),
            ('list,plain', ([1, 2], 'plain', '[1, 2]')),
            ('list,json', ([1, 2], 'json', '[1, 2]')),
            ('list,yaml', ([1, 2], 'yaml', '- 1\n- 2\n')),
            ('dict,plain', ({'a': 1}, 'plain', '{"a": 1}')),
            ('dict,json', ({'a': 1}, 'json', '{"a": 1}')),
            ('dict,yaml', ({'a': 1}, 'yaml', 'a: 1\n')),
        ]
    ]

    output = None
    format_ = None
    expected_result = None

    def test_format_output(self):
        res = cli_base.format_output(self.output, self.format_)
        self.assertEqual(self.expected_result, res)


class SafeTuningBoxApp(cli.TuningBoxApp):
    def __init__(self, client):
        super(SafeTuningBoxApp, self).__init__(
            client=client,
            **self.get_std_streams()
        )

    @staticmethod
    def get_std_streams():
        if bytes is str:
            io_cls = io.BytesIO
        else:
            io_cls = io.StringIO
        return {k: io_cls() for k in ('stdin', 'stdout', 'stderr')}

    def build_option_parser(self, description, version, argparse_kwargs=None):
        parser = super(SafeTuningBoxApp, self).build_option_parser(
            description, version, argparse_kwargs)
        parser.set_defaults(debug=True)
        return parser

    def get_fuzzy_matches(self, cmd):
        # Turn off guessing, we need exact failures in tests
        return []

    def run(self, argv):
        try:
            exit_code = super(SafeTuningBoxApp, self).run(argv)
        except SystemExit as e:
            exit_code = e.code
        assert exit_code == 0


class _BaseCLITest(base.TestCase):
    BASE_URL = 'http://somehost/prefix'

    def setUp(self):
        super(_BaseCLITest, self).setUp()
        client = tb_client.HTTPClient(self.BASE_URL)
        self.req_mock = self.useFixture(req_fixture.Fixture())
        self.cli = SafeTuningBoxApp(client=client)


class TestApp(_BaseCLITest):
    def test_help(self):
        self.cli.run(["--help"])
        self.assertEqual('', self.cli.stderr.getvalue())
        self.assertNotIn('Could not', self.cli.stdout.getvalue())


class TestGet(testscenarios.WithScenarios, _BaseCLITest):
    scenarios = [
        (s[0], dict(zip(('mock_url', 'args', 'expected_result'), s[1])))
        for s in [
            ('global,json', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1',
                '{"hello": "world"}',
            )),
            ('lowlevel,json', (
                '/environments/1/lvl1/value1/resources/1/values?effective',
                'get --env 1 --level lvl1=value1 --resource 1',
                '{"hello": "world"}',
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
            ('key,plain', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key hello --format plain',
                'world',
            )),
            ('key,json', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key hello --format json',
                '{"hello": "world"}',
            )),
            ('key,yaml', (
                '/environments/1/resources/1/values?effective',
                'get --env 1 --resource 1 --key hello --format yaml',
                'hello: world\n',
            )),
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


class TestOverride(TestSet):
    url_last_part = 'overrides'
    cmd = 'override'
