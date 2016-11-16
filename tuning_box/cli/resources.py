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
import six
import yaml

from cliff import show
from fuelclient.cli import error as fc_error
from fuelclient.common import data_utils

from tuning_box.cli.base import BaseCommand
from tuning_box.cli.base import level_converter


class ResourcesCommand(BaseCommand):
    def get_parser(self, *args, **kwargs):
        parser = super(ResourcesCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '-e', '--env',
            type=int,
            required=True,
            help="ID of environment to get data from",
        )
        parser.add_argument(
            '-l', '--level',
            type=level_converter,
            default=[],
            help=("Level to get data from. Should be in format "
                  "parent_level=parent1,level=value2"),
        )
        parser.add_argument(
            '-r', '--resource',
            type=str,
            required=True,
            help="Name or ID of resource to get data from",
        )
        return parser

    def get_resource_url(self, parsed_args, last_part='values'):
        return '/environments/{}/{}resources/{}/{}'.format(
            parsed_args.env,
            ''.join('{}/{}/'.format(*e) for e in parsed_args.level),
            parsed_args.resource,
            last_part,
        )


class Get(show.ShowOne, ResourcesCommand):

    def get_parser(self, *args, **kwargs):
        parser = super(Get, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '-k', '--key',
            type=str,
            help="Name of key to get from the resource. For fetching nested "
                 "key value use '.' as delimiter. Example: k1.k2.k3",
        )
        parser.add_argument(
            '-s', '--show-lookup',
            dest='show_lookup',
            help="Show lookup path for the value in the result",
            action='store_true'
        )
        return parser

    def take_action(self, parsed_args):
        params = {'effective': True}
        if parsed_args.show_lookup:
            params['show_lookup'] = True
        if parsed_args.key:
            params['key'] = parsed_args.key
        response = self.get_client().get(
            self.get_resource_url(parsed_args),
            params=params
        )
        if parsed_args.key:
            result = {parsed_args.key: response}
        else:
            result = response
        columns = sorted(result)
        try:
            data = data_utils.get_display_data_single(columns, result)
            return columns, data
        except fc_error.BadDataException:
            return zip(*response.items())


class Set(ResourcesCommand):

    url_last_part = 'values'
    entity_name = 'ResourceValue'

    def get_parser(self, *args, **kwargs):
        parser = super(Set, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '-k', '--key',
            type=str,
            help="Name of key to set in the resource",
        )
        parser.add_argument(
            '-v', '--value',
            type=str,
            help="Value for a key to set in the resource",
        )
        parser.add_argument(
            '-t', '--type',
            choices=('null', 'int', 'str', 'json', 'yaml', 'bool'),
            help="Type of value passed in --value",
        )
        parser.add_argument(
            '-f', '--format',
            choices=('json', 'yaml'),
            help="Format of data passed to stdin",
        )
        return parser

    def verify_arguments(self, parsed_args):
        if parsed_args.key is None:  # no key
            if parsed_args.value is not None or parsed_args.type is not None:
                raise Exception("--value and --type arguments make sense only "
                                "with --key argument.")
            if parsed_args.format is None:
                raise Exception("Please specify format of data passed to stdin"
                                " to replace whole resource data.")
        elif parsed_args.value is not None:  # have key and value
            if parsed_args.format is not None:
                raise Exception("You shouldn't specify --format if you pass "
                                "value in command line, specify --type "
                                "instead.")
            if parsed_args.type == 'null':
                raise Exception("You shouldn't specify a value for 'null' type"
                                " because there can be only one.")
            if parsed_args.type is None:
                raise Exception("Please specify type of value passed in "
                                "--value argument to properly represent it"
                                " in the storage.")
        elif parsed_args.type != 'null':  # have key but no value
            if parsed_args.type is not None:
                raise Exception("--type specifies type for value provided in "
                                "--value but there is not --value argument")
            if parsed_args.format is None:
                raise Exception("Please specify format of data passed to stdin"
                                " to replace the key.")

    def get_value_to_set(self, parsed_args):
        type_ = parsed_args.type
        if type_ == 'null':
            return None
        elif type_ == 'bool':
            if parsed_args.value.lower() in ('1', 'true'):
                return True
            elif parsed_args.value.lower() in ('0', 'false'):
                return False
            else:
                raise Exception(
                    "Bad value for 'bool' type: '{}'. Should be one of '0', "
                    "'1', 'false', 'true'.".format(parsed_args.value))
        elif type_ == 'int':
            return int(parsed_args.value)
        elif type_ == 'str':
            return parsed_args.value
        elif type_ == 'json':
            return json.loads(parsed_args.value)
        elif type_ == 'yaml':
            return yaml.safe_load(parsed_args.value)
        elif type_ is None:
            if parsed_args.format == 'json':
                return json.load(self.app.stdin)
            elif parsed_args.format == 'yaml':
                docs_gen = yaml.safe_load_all(self.app.stdin)
                doc = next(docs_gen)
                guard = object()
                if next(docs_gen, guard) is not guard:
                    self.app.stderr.write("Warning: will use only first "
                                          "document from YAML stream")
                return doc
        assert False, "Shouldn't get here"

    def get_update_message(self, parsed_args):
        if parsed_args.key is None:
            message = '{0} was set\n'.format(self.entity_name)
        else:
            message = '{0} for key {1} was set\n'.format(
                self.entity_name, parsed_args.key)
        return message

    def take_action(self, parsed_args):
        self.verify_arguments(parsed_args)
        value = self.get_value_to_set(parsed_args)

        client = self.get_client()
        resource_url = self.get_resource_url(parsed_args, self.url_last_part)
        if parsed_args.key is not None:
            resource = client.get(resource_url)
            resource[parsed_args.key] = value
        else:
            resource = value
        result = client.put(resource_url, resource)
        if result is None:
            result = self.get_update_message(parsed_args)
        self.app.stdout.write(six.text_type(result))


class Delete(ResourcesCommand):

    url_last_part = 'values'
    entity_name = 'ResourceValue'

    def get_parser(self, *args, **kwargs):
        parser = super(Delete, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '-k', '--key',
            type=str,
            help="Name of key to delete from the resource",
            required=True
        )
        return parser

    def get_deletion_message(self, parsed_args):
        return '{0} for key {1} was deleted\n'.format(
            self.entity_name, parsed_args.key)

    def get_resource_url(self, parsed_args, last_part='values'):
        url = super(Delete, self).get_resource_url(
            parsed_args, last_part=last_part)
        return url + '/keys/delete'

    def take_action(self, parsed_args):
        client = self.get_client()
        resource_url = self.get_resource_url(parsed_args, self.url_last_part)
        result = client.patch(resource_url, [[parsed_args.key]])
        if result is None:
            result = self.get_deletion_message(parsed_args)
        self.app.stdout.write(six.text_type(result))


class Override(Set):
    url_last_part = 'overrides'
    entity_name = 'ResourceOverride'


class DeleteOverride(Delete):
    url_last_part = 'overrides'
    entity_name = 'ResourceOverride'
