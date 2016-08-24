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

from cliff import show
import six

from tuning_box.cli import base


class ComponentsCommand(base.BaseCommand):
    entity_name = 'component'
    base_url = '/components'
    columns = ('id', 'name', 'resource_definitions')


class ListComponents(ComponentsCommand, base.BaseListCommand):
    pass


class ShowComponent(ComponentsCommand, base.BaseShowCommand):
    pass


class DeleteComponent(ComponentsCommand, base.BaseDeleteCommand):
    pass


class CreateComponent(ComponentsCommand, show.ShowOne):

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
        result = self.get_client().post(
            self.base_url, {'name': parsed_args.name,
                            'resource_definitions': []})
        return zip(*result.items())


class UpdateComponent(ComponentsCommand, base.BaseOneCommand):

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

        result = self.get_client().patch(self.get_url(parsed_args), data)
        if result is None:
            result = self.get_update_message(parsed_args)
        self.app.stdout.write(six.text_type(result))
