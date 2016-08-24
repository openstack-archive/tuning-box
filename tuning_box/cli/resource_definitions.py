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

import json
import yaml

from cliff import show

from tuning_box.cli import base
from tuning_box.cli import errors


class ResourceDefinitionsCommand(base.BaseCommand):
    entity_name = 'resource_definition'
    base_url = '/resource_definitions'
    columns = ('id', 'name', 'component_id', 'content')


class ListResourceDefinitions(ResourceDefinitionsCommand,
                              base.BaseListCommand):
    pass


class ShowResourceDefinition(ResourceDefinitionsCommand,
                             base.BaseShowCommand):
    pass


class DeleteResourceDefinition(ResourceDefinitionsCommand,
                               base.BaseDeleteCommand):
    pass


class ModifyResourceDefinitionCommand(ResourceDefinitionsCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(ModifyResourceDefinitionCommand, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '-n', '--name',
            dest='name',
            type=str,
            help="Resource definition name"
        )
        parser.add_argument(
            '-i', '--component-id',
            dest='component_id',
            type=int,
            help="Component Id"
        )
        parser.add_argument(
            '-p', '--content',
            dest='content',
            type=str,
            help="Content to be set"
        )
        parser.add_argument(
            '-t', '--type',
            choices=('json', 'yaml'),
            help="Content type"
        )
        parser.add_argument(
            '-d', '--data-format',
            dest='data_format',
            choices=('json', 'yaml'),
            help="Format of data passed to stdin to be set to content"
        )
        return parser

    def verify_arguments(self, parsed_args):
        if parsed_args.content is not None:
            if parsed_args.data_format is not None:
                raise errors.IncompatibleParams(
                    "You shouldn't specify --data-format if you pass "
                    "content in command line, specify --type instead."
                )
            elif parsed_args.type is None:
                raise errors.IncompatibleParams(
                    "You should specify --type if you pass "
                    "content in command line."
                )
        elif parsed_args.data_format is None:
            raise errors.IncompatibleParams(
                "You should specify --data-format for stdin data if you "
                "don't pass content in command line."
            )
        elif parsed_args.type is not None:
            raise errors.IncompatibleParams(
                "--type and --data-format parameters can't "
                "be used together."
            )

    def get_content(self, parsed_args):
        type_ = parsed_args.type
        if type_ == 'json':
            return json.loads(parsed_args.content)
        elif type_ == 'yaml':
            return yaml.safe_load(parsed_args.content)
        elif type_ is None:
            data_format = parsed_args.data_format
            if data_format == 'json':
                return self.read_json()
            elif data_format == 'yaml':
                return self.read_yaml()
            raise errors.UnsupportedDataType(
                "Unsupported format: {0}".format(data_format)
            )
        raise errors.UnsupportedDataType("Unsupported type: {0}".format(type_))


class CreateResourceDefinition(ModifyResourceDefinitionCommand, show.ShowOne):

    def take_action(self, parsed_args):
        self.verify_arguments(parsed_args)
        data = {
            'name': parsed_args.name,
            'component_id': parsed_args.component_id,
            'content': self.get_content(parsed_args)
        }
        result = self.get_client().post(self.base_url, data)
        return zip(*result.items())


class UpdateResourceDefinition(ModifyResourceDefinitionCommand,
                               base.BaseOneCommand):

    def take_action(self, parsed_args):
        data = {}
        if parsed_args.name is not None:
            data['name'] = parsed_args.name
        if parsed_args.component_id is not None:
            data['component_id'] = parsed_args.component_id
        if (parsed_args.content is not None
                or parsed_args.data_format is not None):
            data['content'] = self.get_content(parsed_args)

        self.get_client().patch(self.get_url(parsed_args), data)
        return self.get_update_message(parsed_args)
