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
from cliff import lister
from fuelclient.common import data_utils
from fuelclient.cli import error as fc_error
import six

from tuning_box.cli import base


class HierarchyLevelsCommand(base.BaseCommand):
    columns = ('id', 'name', 'parent', 'values')

    def get_parser(self, *args, **kwargs):
        parser = super(ListHierarchyLevels, self).get_parser(
            *args, **kwargs)
        parser.add_argument(
            '-e', '--env',
            type=int,
            required=True,
            help="ID of environment to get data from",
        )
        return parser

    def get_base_url(self, parsed_args):
        return '/environments/{}/hierarchy_levels'.format(parsed_args.env)


class ListHierarchyLevels(HierarchyLevelsCommand, lister.Lister):

    def take_action(self, parsed_args):
        result = self.get_client().get(self.get_base_url(parsed_args))
        try:
            data = data_utils.get_display_data_multi(self.columns, result)
            return self.columns, data
        except fc_error.BadDataException:
            return zip(*result.items())


class ShowHierarchyLevels(HierarchyLevelsCommand, show.ShowOne):

    def get_parser(self, *args, **kwargs):
        parser = super(ShowHierarchyLevels, self).get_parser(*args, **kwargs)
        parser.add_argument(
            'id',
            type=int,
            help='Id of the {0}'.format(self.entity_name),
            required=True
        )
        return parser

    def take_action(self, parsed_args):
        result = self.get_client().get(self.get_url(parsed_args))
        try:
            data = data_utils.get_display_data_single(self.columns, result)
            return self.columns, data
        except fc_error.BadDataException:
            return zip(*result.items())
