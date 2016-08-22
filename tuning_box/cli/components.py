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

from tuning_box.cli.base import BaseCommand


class ComponentsCommand(BaseCommand):
    def get_parser(self, *args, **kwargs):
        parser = super(ComponentsCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '--component',
            type=int,
            required=True,
            help="ID of component to get data from"
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

    def get_component_url(self, parsed_args):
        return '/components/{}'.format(parsed_args.component)
