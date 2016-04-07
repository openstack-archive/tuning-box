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


class Get(base.FormattedCommand, base.ResourceCommand):
    def get_parser(self, *args, **kwargs):
        parser = super(Get, self).get_parser(*args, **kwargs)
        parser.add_argument(
            '--key',
            type=str,
            help="Name of key to get from the resource",
        )
        return parser

    def take_action(self, parsed_args):
        res = self.get_client().get(
            self.get_resource_url(parsed_args),
            params='effective',
        )
        key = parsed_args.key
        if key is None:
            return res
        value = res[key]
        if parsed_args.format != 'plain':
            return {key: value}
        else:
            return value
