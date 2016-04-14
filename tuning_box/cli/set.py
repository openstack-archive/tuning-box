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

from tuning_box.cli import base


class Set(base.ResourceCommand):
    url_last_part = 'values'

    def get_parser(self, *args, **kwargs):
        parser = super(Set, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '--key',
            type=str,
            help="Name of key to set in the resource",
        )
        parser.add_argument(
            '--value',
            type=str,
            help="Value for a key to set in the resource",
        )
        parser.add_argument(
            '--type',
            choices=('null', 'int', 'str', 'json', 'yaml', 'bool'),
            help="Tyep of value passed in --value",
        )
        parser.add_argument(
            '--format',
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
        client.put(resource_url, resource)


class Override(Set):
    url_last_part = 'overrides'
