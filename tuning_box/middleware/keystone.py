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

from keystonemiddleware import auth_token


class KeystoneMiddleware(auth_token.AuthProtocol):

    def __init__(self, app):
        self.app = app.wsgi_app
        auth_settings = app.config.get('AUTH')
        super(KeystoneMiddleware, self).__init__(self.app, auth_settings)
