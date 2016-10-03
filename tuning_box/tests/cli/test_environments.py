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
from tuning_box.cli import environments as env
from tuning_box.tests import cli as tests_cli


class TestCreateEnvironment(tests_cli.BaseCommandTest):

    cmd = env.CreateEnvironment(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            (),
            ('-i1',),
            ('-i1,2',),
            ('-i1', '-llvl1'),
            ('-i1', '-llvl1,lvl2'),
            ('--components=1,2', '--levels=lvl1,lvl2')
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-i1', '-llvl1,lvl2'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            m_client.post.return_value = {'a': 1, 'b': 2}
            self.cmd.run(parsed_params)
            m_client.post.assert_called_with(
                '/environments',
                {'hierarchy_levels': ['lvl1', 'lvl2'], 'components': [1]}
            )


class TestListEnvironments(tests_cli.BaseCommandTest):

    cmd = env.ListEnvironments(tests_cli.SafeTuningBoxApp(), None)

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
                {'id': 1, 'hierarchy_levels': [], 'components': [1, 2]}
            ]
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with('/environments')


class TestShowEnvironment(tests_cli.BaseCommandTest):

    cmd = env.ShowEnvironment(tests_cli.SafeTuningBoxApp(), None)

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
            m_client.get.return_value = {'id': 1, 'hierarchy_levels': [],
                                         'components': [1, 2]}
            self.cmd.run(parsed_params)
            m_client.get.assert_called_with('/environments/3')


class TestDeleteEnvironment(tests_cli.BaseCommandTest):

    cmd = env.DeleteEnvironment(tests_cli.SafeTuningBoxApp(), None)

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
            m_client.delete.assert_called_with('/environments/3')


class TestUpdateEnvironment(tests_cli.BaseCommandTest):

    cmd = env.UpdateEnvironment(tests_cli.SafeTuningBoxApp(), None)

    def test_arguments(self):
        params_set = [
            ('1',),
            ('-l[]', '1'),
            ('-llvl1', '-i1', '1'),
            ('-llvl1,lvl2', '-i1', '1'),
            ('-llvl1,lvl2', '-i1,2', '1')
        ]
        for params in params_set:
            self.parser.parse_args(params)

    def test_result(self):
        parsed_params = self.parser.parse_args(('-i1', '-l[]', '1'))
        with mock.patch.object(cli_base.BaseCommand, 'get_client') as client:
            m_client = mock.Mock()
            client.return_value = m_client
            self.cmd.run(parsed_params)
            m_client.patch.assert_called_with(
                '/environments/1',
                {'hierarchy_levels': [], 'components': [1]}
            )
