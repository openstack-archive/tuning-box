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

import itertools

from werkzeug import routing
from werkzeug import urls

from tuning_box.library import resource_keys_operation


class Levels(routing.BaseConverter):
    """Converter that maps nested levels to list of tuples.

    For example, "level1/value1/level2/value2/" is mapped to
    [("level1", "value1"), ("level2", "value2")].

    Note that since it can be empty it includes following "/":

        Rule('/smth/<levels:levels>values')

    will parse "/smth/values" and "/smth/level1/value1/values".
    """

    regex = "([^/]+/[^/]+/)*"

    def to_python(self, value):
        spl = value.split('/')
        return list(zip(spl[::2], spl[1::2]))

    def to_url(self, value):
        parts = itertools.chain.from_iterable(value)
        quoted_parts = (urls.url_quote(p, charset=self.map.charset, safe='')
                        for p in parts)
        return ''.join(p + '/' for p in quoted_parts)


class IdOrName(routing.BaseConverter):
    """Converter that matches either int or URL part including "/" as string"""

    regex = '[^/].*?'

    def to_python(self, value):
        try:
            return int(value)
        except ValueError:
            return value

    def to_url(self, value):
        return super(IdOrName, self).to_url(str(value))


class KeysOperation(routing.BaseConverter):
    """Converter that matches keys operations

    Allowed operations: add, delete, erase
    """

    regex = '(' + ')|('.join(
        resource_keys_operation.KeysOperationMixin.OPERATIONS
    ) + ')'


ALL = {
    'levels': Levels,
    'id_or_name': IdOrName,
    'keys_operation': KeysOperation
}
