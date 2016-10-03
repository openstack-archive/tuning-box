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

import mock

from tuning_box.cli import base as cli_base
from tuning_box.cli import errors
from tuning_box.cli import resource_definitions as res_def
from tuning_box.tests import cli as tests_cli


class TestCreateResourceDefinition(tests_cli.BaseCommandTest):

    cmd = res_def.CreateResourceDefinition(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('-nname',),
            ('-nname', '-fjson'),
            ('-nname', '-fyaml'),
            ('-nname', '-djson'),
            ('-nname', '-dyaml'),
            ('-nname', '-i1'),
            ('-nname', '-i1', '-djson'),
            ('-nname', '-i1', '-tjson', '-pa'),
            ('--name=a', '--component=1', '--type=json', '--content=a'),
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_arguments_constraints(self):
        params_set = [
            ('-na', '-px', '-djson'),  # should use type
            ('-na', '-px'),  # should use type
            ('-na',),  # no data format
            ('-na', '-tjson', '-djson'),  # type and content-data
        ]
        for params in params_set:
            parsed_params = self.parser.parse_args(params)
            self.assertRaises(errors.IncompatibleParams, self.cmd.run,
                              parsed_params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-na', '-i1', '-p"aaa"',
                                                '-tjson'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.post.return_value = {'a': 1, 'b': 2}
            self.cmd.run(parsed_params)
            m_client.post.assert_called_with(
                '/resource_definitions',
                {'content': 'aaa', 'component_id': 1, 'name': 'a'}
            )


class TestListResourceDefinitions(tests_cli.BaseCommandTest):

    cmd = res_def.ListResourceDefinitions(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('-fjson',),
            ('-fyaml',),
            ('-ftable',),
            ('-fvalue',),
            ('-fcsv',),
            ('-cid',),
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(())
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.get.return_value = [
                {'id': 1, 'name': 'n', 'component_id': 1, 'content': 'xx'}
            ]
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with('/resource_definitions')


class TestShowComponent(tests_cli.BaseCommandTest):

    cmd = res_def.ShowResourceDefinition(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('-fjson', '1'),
            ('-fyaml', '1'),
            ('-ftable', '1'),
            ('-fvalue', '1'),
            ('-fshell', '1'),
            ('-cid', '1'),
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('3',))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.get.return_value = {'id': 1, 'name': 'n',
                                         'component_id': 1, 'content': 'xx'}
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with('/resource_definitions/3')


class TestDeleteComponent(tests_cli.BaseCommandTest):

    cmd = res_def.DeleteResourceDefinition(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [('1',)]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('3',))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            self.cmd.run(parsed_params)
            m_client.delete.assert_called_with('/resource_definitions/3')


class TestUpdateResourceDefinition(tests_cli.BaseCommandTest):

    cmd = res_def.UpdateResourceDefinition(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('-nname', '1'),
            ('-nname', '-i1', '1'),
            ('-nname', '-i1', '-pval', '1'),
            ('-nname', '-i1', '-pval', '-tjson', '1'),
            ('-nname', '-i1', '-pval', '-tyaml', '1'),
            ('-nname', '-i1', '-djson', '1'),
            ('-nname', '-i1', '-dyaml', '1'),
            ('--name=a', '--component-id=1', '--type=json',
             '--content=a', '1'),
            ('--name=a', '--component-id=1', '--data-format=json', '1')
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_arguments_constraints(self):
        params_set = [
            ('-px', '1'),  # no type
            ('-px', '-djson', '1'),  # should use type
            ('-px', '-djson', '-tjson', '1'),  # shouldn't use data-format
            ('-tjson', '1'),  # no content
        ]

        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            data = {'a': 'b'}
            json.dump(data, self.cmd.app.stdin)

            for params in params_set:
                parsed_params = self.parser.parse_args(params)
                self.cmd.app.stdin.seek(io.SEEK_SET)
                self.assertRaises(errors.IncompatibleParams, self.cmd.run,
                                  parsed_params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-na', '-i1', '-p"aaa"',
                                                '-tjson', '1'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            self.cmd.run(parsed_params)
            m_client.patch.assert_called_with(
                '/resource_definitions/1',
                {'content': 'aaa', 'component_id': 1, 'name': 'a'}
            )
