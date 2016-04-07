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

from cliff import command
import yaml


def level_converter(value):
    levels = []
    for part in value.split(','):
        spl = part.split("=", 1)
        if len(spl) != 2:
            raise TypeError("Levels list should be in format "
                            "level1=value1,level2=value2")
        levels.append(tuple(spl))
    return levels

try:
    text_type = unicode
except NameError:
    text_type = str


def format_output(output, format_):
    if format_ == 'plain':
        if output is None:
            return ''
        if isinstance(output, text_type):
            if text_type is str:
                return output
            else:
                return output.encode('utf-8')
        format_ = 'json'
        # numbers, booleans, lists and dicts will be represented as JSON
    if format_ == 'json':
        return json.dumps(output)
    if format_ == 'yaml':
        # Usage of safe_dump here is crucial since PyYAML emits
        # "!!python/unicode" objects from unicode strings by defaul
        return yaml.safe_dump(output, default_flow_style=False)
    raise RuntimeError("Unknown format '{}'".format(format_))


class BaseCommand(command.Command):
    def get_client(self):
        return self.app.client


class FormattedCommand(BaseCommand):
    format_choices = ('json', 'yaml', 'plain')

    def get_parser(self, *args, **kwargs):
        parser = super(FormattedCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '--format',
            choices=self.format_choices,
            default='json',
            help="Desired format for return value",
        )
        return parser

    def run(self, parsed_args):
        res = self.take_action(parsed_args)
        self.app.stdout.write(format_output(res, parsed_args.format))
        return 0


class ResourceCommand(BaseCommand):
    def get_parser(self, *args, **kwargs):
        parser = super(ResourceCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '--env',
            type=int,
            required=True,
            help="ID of environment to get data from",
        )
        parser.add_argument(
            '--level',
            type=level_converter,
            default=[],
            help=("Level to get data from. Should be in format "
                  "parent_level=parent1,level=value2"),
        )
        parser.add_argument(
            '--resource',
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
