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

from tuning_box.cli import base as cli_base
from tuning_box.cli import components
from tuning_box.tests import cli as tests_cli


class TestCreateComponent(tests_cli.BaseCommandTest):

    cmd = components.CreateComponent(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            (),
            ('-na',),
            ('-na', '-fjson'),
            ('-na', '-fyaml'),
            ('-na', '-ftable'),
            ('-na', '-fshell'),
            ('-na', '-fvalue'),
            ('--name=a', '--format=json')
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-na',))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.post.return_value = {'a': 1, 'b': 2}
            self.cmd.run(parsed_params)
            m_client.post.assert_called_with(
                '/components',
                {'resource_definitions': [], 'name': 'a'}
            )


class TestListComponents(tests_cli.BaseCommandTest):

    cmd = components.ListComponents(tests_cli.SafeTuningBoxApp(), None)

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
                {'id': 1, 'resource_definitions': [1, 2], 'name': 'n'}
            ]
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with('/components')


class TestShowComponent(tests_cli.BaseCommandTest):

    cmd = components.ShowComponent(tests_cli.SafeTuningBoxApp(), None)

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
                                         'resource_definitions': [1, 2]}
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with('/components/3')


class TestDeleteComponent(tests_cli.BaseCommandTest):

    cmd = components.DeleteComponent(tests_cli.SafeTuningBoxApp(), None)

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
            m_client.delete.assert_called_with('/components/3')


class TestUpdateComponent(tests_cli.BaseCommandTest):

    cmd = components.UpdateComponent(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('1',),
            ('-r[]', '1'),
            ('-r1,2', '1'),
            ('-na', '-r1,2', '1')
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-na', '-r[]', '1'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            self.cmd.run(parsed_params)
            m_client.patch.assert_called_with(
                '/components/1',
                {'name': 'a', 'resource_definitions': []}
            )
