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

from tuning_box.cli import base
from tuning_box.cli.base import BaseCommand


class ListComponents(base.FormattedCommand, BaseCommand):

    def take_action(self, parsed_args):
        return self.get_client().get('/components')


class CreateComponent(base.FormattedCommand, BaseCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(CreateComponent, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '-n', '--name',
            type=str,
            help="Component name"
        )
        return parser

    def take_action(self, parsed_args):
        return self.get_client().post(
            '/components', {'name': parsed_args.name,
                            'resource_definitions': []})


class ComponentCommand(base.FormattedCommand, BaseCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(ComponentCommand, self).get_parser(*args, **kwargs)
        parser.add_argument('id', type=int, help='Id of the component')
        return parser


class ShowComponent(ComponentCommand):

    def take_action(self, parsed_args):
        return self.get_client().get('/components/{0}'.format(
            parsed_args.id))


class DeleteComponent(ComponentCommand):

    def take_action(self, parsed_args):
        return self.get_client().delete('/components/{0}'.format(
            parsed_args.id))


class UpdateComponent(ComponentCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(UpdateComponent, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '-n', '--name',
            type=str,
            help="Component name"
        )
        parser.add_argument(
            '-r', '--resource-definitions',
            dest='resources',
            type=str,
            help="Comma separated resource definitions IDs. "
                 "Set parameter to [] if you want to pass empty list",
        )
        return parser

    def take_action(self, parsed_args):
        data = {}
        if parsed_args.name is not None:
            data['name'] = parsed_args.name
        if parsed_args.resources is not None:
            data['resource_definitions'] = []
            res_def_ids = self._parse_comma_separated(
                parsed_args, 'resources', int)
            for res_def_id in res_def_ids:
                data['resource_definitions'].append({'id': res_def_id})

        return self.get_client().patch(
            '/components/{0}'.format(parsed_args.id),
            data
        )
