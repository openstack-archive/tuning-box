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

import abc
import json
import yaml

from cliff import command
import six


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

    def _parse_comma_separated(self, parsed_args, param_name, cast_to):
        param = getattr(parsed_args, param_name)
        if param is None or param == '[]':
            return []
        result = six.moves.map(six.text_type.strip,
                               six.text_type(param).split(','))
        return list(six.moves.map(cast_to, result))


class BaseOneCommand(BaseCommand):

    @abc.abstractproperty
    def base_url(self):
        """Base url for request operations"""

    @abc.abstractproperty
    def entity_name(self):
        """Name of the TuningBox entity"""

    def get_parser(self, *args, **kwargs):
        parser = super(BaseOneCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            'id',
            type=int,
            help='Id of the {0} to delete.'.format(self.entity_name))
        return parser

    def get_url(self, parsed_args):
        return '{0}/{1}'.format(self.base_url, parsed_args.id)

    def get_deletion_message(self, parsed_args):
        return '{0} with id {1} was deleted'.format(
            self.entity_name.capitalize(), parsed_args.id)

    def get_update_message(self, parsed_args):
        return '{0} with id {1} was updated'.format(
            self.entity_name.capitalize(), parsed_args.id)


class BaseDeleteCommand(BaseOneCommand):
    """Deletes entity with the specified id."""

    def take_action(self, parsed_args):
        self.get_client().delete(self.get_url(parsed_args))
        return self.get_deletion_message(parsed_args)


class FormattedCommand(BaseCommand):
    format_choices = ('json', 'yaml', 'plain')

    def get_parser(self, *args, **kwargs):
        parser = super(FormattedCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '-f', '--format',
            choices=self.format_choices,
            default='json',
            help="Desired format for return value",
        )
        return parser

    def run(self, parsed_args):
        res = self.take_action(parsed_args)
        self.app.stdout.write(format_output(res, parsed_args.format))
        return 0
