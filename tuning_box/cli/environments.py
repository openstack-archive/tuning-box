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

import six

from tuning_box.cli import base
from tuning_box.cli.base import BaseCommand


class ListEnvironments(base.FormattedCommand, BaseCommand):

    def take_action(self, parsed_args):
        return self.get_client().get('/environments')


class CreateEnvironment(base.FormattedCommand, BaseCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(CreateEnvironment, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '--components',
            type=str,
            help="Comma separated components IDs",
        )
        parser.add_argument(
            '--levels',
            type=str,
            help="Comma separated levels names",
        )
        return parser

    def take_action(self, parsed_args):
        levels = self._parse_comma_separated(
            parsed_args, 'levels', six.text_type)
        components = self._parse_comma_separated(
            parsed_args, 'components', int)
        res = self.get_client().post(
            '/environments',
            {'hierarchy_levels': levels, 'components': components}
        )
        return res


class EnvironmentCommand(base.FormattedCommand, BaseCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(EnvironmentCommand, self).get_parser(*args, **kwargs)
        parser.add_argument('id', type=int, help='Id of the environment')
        return parser


class ShowEnvironment(EnvironmentCommand):

    def take_action(self, parsed_args):
        return self.get_client().get('/environments/{0}'.format(
            parsed_args.id))


class DeleteEnvironment(EnvironmentCommand):

    def take_action(self, parsed_args):
        return self.get_client().delete('/environments/{0}'.format(
            parsed_args.id))
