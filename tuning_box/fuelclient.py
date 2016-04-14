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

from __future__ import absolute_import

from cliff import command
from fuelclient import client as fc_client

from tuning_box import cli
from tuning_box.cli import base as cli_base
from tuning_box.cli import get as cli_get
from tuning_box.cli import set as cli_set
from tuning_box import client as tb_client


class FuelHTTPClient(tb_client.HTTPClient):
    def __init__(self):
        service_catalog = fc_client.APIClient.keystone_client.service_catalog
        base_url = service_catalog.url_for(
            service_type='config',
            endpoint_type='publicURL',
        )
        super(FuelHTTPClient, self).__init__(base_url)

    def default_headers(self):
        headers = super(FuelHTTPClient, self).default_headers()
        if fc_client.APIClient.auth_token:
            headers['X-Auth-Token'] = fc_client.APIClient.auth_token
        return headers


class FuelBaseCommand(cli_base.BaseCommand):
    def get_client(self):
        return FuelHTTPClient()


class Get(FuelBaseCommand, cli_get.Get):
    pass


class Set(FuelBaseCommand, cli_set.Set):
    pass


class Override(FuelBaseCommand, cli_set.Override):
    pass


class Config(command.Command):
    def get_parser(self, *args, **kwargs):
        parser = super(Config, self).get_parser(*args, **kwargs)
        parser.add_argument('args', nargs='*')
        return parser

    def take_action(self, parsed_args):
        client = FuelHTTPClient()
        app = cli.TuningBoxApp(client)
        app.run(parsed_args.args)
