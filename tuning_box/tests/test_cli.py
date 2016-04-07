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

import io

from requests_mock.contrib import fixture as req_fixture

from tuning_box import cli
from tuning_box import client as tb_client
from tuning_box.tests import base


class SafeTuningBoxApp(cli.TuningBoxApp):
    def __init__(self, client):
        super(SafeTuningBoxApp, self).__init__(
            client=client,
            **self.get_std_streams()
        )

    @staticmethod
    def get_std_streams():
        if bytes is str:
            io_cls = io.BytesIO
        else:
            io_cls = io.StringIO
        return {k: io_cls() for k in ('stdin', 'stdout', 'stderr')}

    def build_option_parser(self, description, version, argparse_kwargs=None):
        parser = super(SafeTuningBoxApp, self).build_option_parser(
            description, version, argparse_kwargs)
        parser.set_defaults(debug=True)
        return parser

    def get_fuzzy_matches(self, cmd):
        # Turn off guessing, we need exact failures in tests
        return []

    def run(self, argv):
        try:
            exit_code = super(SafeTuningBoxApp, self).run(argv)
        except SystemExit as e:
            exit_code = e.code
        assert exit_code == 0


class _BaseCLITest(base.TestCase):
    BASE_URL = 'http://somehost/prefix'

    def setUp(self):
        super(_BaseCLITest, self).setUp()
        client = tb_client.HTTPClient(self.BASE_URL)
        self.req_mock = self.useFixture(req_fixture.Fixture())
        self.cli = SafeTuningBoxApp(client=client)


class TestApp(_BaseCLITest):
    def test_help(self):
        self.cli.run(["--help"])
        self.assertEqual('', self.cli.stderr.getvalue())
        self.assertNotIn('Could not', self.cli.stdout.getvalue())
