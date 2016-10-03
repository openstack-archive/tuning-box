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

import unittest

from cliff import app
from cliff import commandmanager
import six


class SafeTuningBoxApp(app.App):
    def __init__(self):
        super(SafeTuningBoxApp, self).__init__(
            description='Tuning Box - configuration storage for your cloud',
            version='',
            command_manager=commandmanager.CommandManager('fuelclient'),
            **self.get_std_streams()
        )

    @staticmethod
    def get_std_streams():
        if bytes is str:
            io_cls = six.BytesIO
        else:
            io_cls = six.StringIO
        return {k: io_cls() for k in ('stdin', 'stdout', 'stderr')}


class BaseCommandTest(unittest.TestCase):

    @property
    def parser(self):
        return self.cmd.get_parser(None)
