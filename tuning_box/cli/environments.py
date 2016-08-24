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


class EnvironmentsCommand(base.BaseCommand):
    entity_name = 'environment'
    base_url = '/environments'
    columns = ('id',)


class ListEnvironments(EnvironmentsCommand, base.BaseListCommand):
    pass


class ShowEnvironment(EnvironmentsCommand, base.BaseShowCommand):
    pass


class DeleteEnvironment(EnvironmentsCommand, base.BaseDeleteCommand):
    pass


class CreateEnvironment(EnvironmentsCommand, show.ShowOne):

    def get_parser(self, *args, **kwargs):
        parser = super(CreateEnvironment, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '-i', '--components',
            type=str,
            help="Comma separated components IDs",
        )
        parser.add_argument(
            '-l', '--levels',
            type=str,
            help="Comma separated levels names",
        )
        return parser

    def take_action(self, parsed_args):
        levels = self._parse_comma_separated(
            parsed_args, 'levels', six.text_type)
        components = self._parse_comma_separated(
            parsed_args, 'components', int)

        result = self.get_client().post(
            self.base_url,
            {'hierarchy_levels': levels, 'components': components}
        )
        return zip(*result.items())


class UpdateEnvironment(EnvironmentsCommand, base.BaseOneCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(UpdateEnvironment, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '-c', '--components',
            dest='components',
            type=str,
            help="Comma separated components IDs. "
                 "Set parameter to [] if you want to pass empty list",
        )
        parser.add_argument(
            '-l', '--levels',
            type=str,
            dest='levels',
            help="Comma separated levels names "
                 "Set parameter to [] if you want to pass empty list",
        )
        return parser

    def take_action(self, parsed_args):
        data = {}
        if parsed_args.levels is not None:
            data['hierarchy_levels'] = self._parse_comma_separated(
                parsed_args, 'levels', six.text_type)
        if parsed_args.components is not None:
            data['components'] = self._parse_comma_separated(
                parsed_args, 'components', int)

        result = self.get_client().patch(self.get_url(parsed_args), data)
        if result is None:
            result = self.get_update_message(parsed_args)
        self.app.stdout.write(six.text_type(result))
