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

import flask
import flask_restful
import itertools

from tuning_box import db
from tuning_box import library
from tuning_box.library import hierarchy_levels
from tuning_box.library import resource_keys_operation


class ResourceValues(flask_restful.Resource):

    @db.with_transaction
    def put(self, environment_id, levels, resource_id_or_name):
        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)

        if res_def.id != resource_id_or_name:
            from tuning_box.app import api
            return flask.redirect(api.url_for(
                ResourceValues,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=res_def.id,
            ), code=308)

        level_value = hierarchy_levels.get_environment_level_value(
            environment, levels)
        esv = db.get_or_create(
            db.ResourceValues,
            environment=environment,
            resource_definition=res_def,
            level_value=level_value,
        )
        esv.values = flask.request.json
        return None, 204

    @db.with_transaction
    def get(self, environment_id, resource_id_or_name, levels):
        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)
        if res_def.id != resource_id_or_name:
            from tuning_box.app import api
            url = api.url_for(
                ResourceValues,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=res_def.id,
            )
            if flask.request.query_string:
                qs = flask.request.query_string.decode('utf-8')
                url += '?' + qs
            return flask.redirect(url, code=308)

        level_values = list(hierarchy_levels.iter_environment_level_values(
            environment, levels))

        if 'effective' in flask.request.args:
            show_lookup = 'show_lookup' in flask.request.args
            resource_values = db.ResourceValues.query.filter_by(
                resource_definition=res_def,
                environment=environment,
            ).all()
            result = {}
            lookup_path = ''
            for level_value in itertools.chain([None], level_values):
                if level_value is not None:
                    name = level_value.level.name
                    value = level_value.value
                    lookup_path += name + '/' + value + '/'
                else:
                    lookup_path += '/'

                for resource_value in resource_values:
                    if resource_value.level_value == level_value:
                        if show_lookup:
                            values = {}
                            for k, v in resource_value.values.items():
                                values[k] = (v, lookup_path)
                            overrides = {}
                            for k, v in resource_value.overrides.items():
                                overrides[k] = (v, lookup_path)
                        else:
                            values = resource_value.values
                            overrides = resource_value.overrides
                        result.update(values)
                        result.update(overrides)
                        break
            return result
        else:
            if not level_values:
                level_value = None
            else:
                level_value = level_values[-1]
            resource_values = db.ResourceValues.query.filter_by(
                resource_definition=res_def,
                environment=environment,
                level_value=level_value,
            ).one_or_none()
            if not resource_values:
                return {}
            return resource_values.values


class ResourceValuesKeys(flask_restful.Resource,
                         resource_keys_operation.ResourceKeysMixin):

    def put(self, environment_id, levels, resource_id_or_name, operation):
        return self.patch(environment_id, levels,
                          resource_id_or_name, operation)

    def patch(self, environment_id, levels, resource_id_or_name, operation):
        self._do_update(environment_id, levels, resource_id_or_name,
                        operation, 'values')
        return None, 204
