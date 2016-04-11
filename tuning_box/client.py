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

import requests


class HTTPClient(object):
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = self.get_session()

    def get_session(self):
        session = requests.Session()
        session.headers.update(self.default_headers())
        return session

    def default_headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def request(self, method, url, **kwargs):
        full_url = self.base_url + url
        resp = self.session.request(method, full_url, **kwargs)
        resp.raise_for_status()
        if resp.headers.get('Content-Type') == 'application/json' and \
                resp.content:
            return resp.json()
        else:
            return None

    def get(self, url, params=None):
        return self.request('GET', url, params=params)

    def put(self, url, body):
        return self.request('PUT', url, json=body)
