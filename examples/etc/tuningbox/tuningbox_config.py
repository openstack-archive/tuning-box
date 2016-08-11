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

LOG_LEVEL = 'DEBUG'
PROPAGATE_EXCEPTIONS = True

SQLALCHEMY_DATABASE_URI = \
    'postgresql://tuningbox:tuningbox@localhost/tuningbox'

AUTH = {
    'auth_host': '127.0.0.1',
    'auth_protocol': 'http',
    'auth_version': 'v2.0',
    'admin_user': 'tuningbox',
    'admin_password': 'tuningbox',
    'admin_tenant_name': 'services'
}
