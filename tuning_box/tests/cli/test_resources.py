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
import json
import unittest

import mock

from tuning_box.cli import base as cli_base
from tuning_box.cli import errors
from tuning_box.cli import resources
from tuning_box.tests import cli as tests_cli


class TestLevelsConverter(unittest.TestCase):

    def test_levels(self):
        params_set = [
            ('lvl=val', [('lvl', 'val')]),
            ('lvl1=val1,lvl2=val2', [('lvl1', 'val1'), ('lvl2', 'val2')]),
            ('lvl1=foo=baz', [('lvl1', 'foo=baz')])
        ]
        for params, expected in params_set:
            actual = cli_base.level_converter(params)
            self.assertEqual(actual, expected)

    def test_levels_failure(self):
        params_set = [
            ('', TypeError),
            ('val', TypeError),
            ('lvl1=val2,val', TypeError)
        ]
        for params, expected in params_set:
            self.assertRaises(expected, cli_base.level_converter, params)


class TestGet(tests_cli.BaseCommandTest):

    cmd = resources.Get(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('-e1', '-r1'),
            ('-e1', '-r1', '-fjson'),
            ('-e1', '-r1', '-fyaml'),
            ('-e1', '-r1', '-ftable'),
            ('-e1', '-r1', '-fshell'),
            ('-e1', '-r1', '-fvalue'),
            ('-e1', '-r1', '-la=1'),
            ('-e1', '-r1', '-la=1,b=2'),
            ('-e1', '-r1', '-la=1,b=2', '-kkey'),
            ('-e1', '-r1', '-la=1,b=2', '-s'),
            ('--env=1', '--resource=1', '--format=json', '--level=a=1'
             '--key=kk', '--show-lookup'),
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-e1', '-r1', '-fjson'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.get.return_value = {'a': 1, 'b': 2}
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with(
                '/environments/1/resources/1/values',
                params={'effective': True}
            )


class TestSet(tests_cli.BaseCommandTest):

    cmd = resources.Set(tests_cli.SafeTuningBoxApp(), None)
    url_end = 'values'

    def test_arguments(self):
        params_set = [
            ('-e1', '-r1'),
            ('-e1', '-r1', '-fjson'),
            ('-e1', '-r1', '-fyaml'),
            ('-e1', '-r1', '-fjson'),
            ('-e1', '-r1', '-tnull'),
            ('-e1', '-r1', '-tint'),
            ('-e1', '-r1', '-tstr'),
            ('-e1', '-r1', '-tjson'),
            ('-e1', '-r1', '-tyaml'),
            ('-e1', '-r1', '-tbool'),
            ('-e1', '-r1', '-la=1,b=2'),
            ('-e1', '-r1', '-la=1,b=2', '-kkey'),
            ('-e1', '-r1', '-la=1,b=2', '-kkey', '-vval'),
            ('--env=1', '--resource=1', '--level=a=1,b=2', '--key=key',
             '--value=val')
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_arguments_constraints(self):
        params_set = [
            ('-e1', '-r1', '-tint'),  # no key
            ('-e1', '-r1', '-vval'),  # no key
            ('-e1', '-r1', '-tstr', '-vval'),  # no key
            ('-e1', '-r1', '-kk', '-vval', '-fjson'),  # should use type
            ('-e1', '-r1', '-kk', '-tstr', '-fjson'),  # no val
        ]
        for params in params_set:
            parsed_params = self.parser.parse_args(params)
            self.assertRaises(errors.IncompatibleParams, self.cmd.run,
                              parsed_params)

    def test_result_no_key(self):
        parsed_params = self.parser.parse_args(('-e1', '-r1', '-fjson'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            data = {'a': 'b'}
            json.dump(data, self.cmd.app.stdin)
            self.cmd.app.stdin.seek(io.SEEK_SET)
            self.cmd.run(parsed_params)
            m_client.put.assert_called_with(
                '/environments/1/resources/1/{0}'.format(self.url_end),
                data
            )

    def test_result_with_key(self):
        parsed_params = self.parser.parse_args(('-e1', '-r1', '-kkey',
                                                '-tjson', '-v{"a": "b"}'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.get.return_value = {'init': 'value'}
            self.cmd.run(parsed_params)
            m_client.put.assert_called_with(
                '/environments/1/resources/1/{0}'.format(self.url_end),
                {'init': 'value', 'key': {'a': 'b'}}
            )


class TestOverride(tests_cli.BaseCommandTest):

    cmd = resources.Override(tests_cli.SafeTuningBoxApp(), None)
    url_end = 'overrides'


class TestDelete(tests_cli.BaseCommandTest):

    cmd = resources.Delete(tests_cli.SafeTuningBoxApp(), None)
    url_end = 'values'

    def test_arguments(self):
        params_set = [
            ('-e1', '-r1', '-la=1,b=2', '-kkey'),
            ('--env=1', '--resource=1', '--level=a=1', '--key=k'),
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-e1', '-r1', '-la=1,b=2',
                                                '-kkey'))
        url = '/environments/1/a/1/b/2/resources/1/{0}/keys/delete'.format(
            self.url_end)
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            self.cmd.run(parsed_params)
            m_client.patch.assert_called_with(url, [['key']])


class TestDeleteOverride(TestDelete):

    cmd = resources.DeleteOverride(tests_cli.SafeTuningBoxApp(), None)
    url_end = 'overrides'
