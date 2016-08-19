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

from tuning_box import db
from tuning_box import library
from tuning_box.library import hierarchy_levels
from tuning_box.library import resource_keys_operation


class ResourceOverrides(flask_restful.Resource):

    @db.with_transaction
    def put(self, environment_id, levels, resource_id_or_name):
        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)
        if res_def.id != resource_id_or_name:
            from tuning_box.app import api
            return flask.redirect(api.url_for(
                ResourceOverrides,
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
        esv.overrides = flask.request.json
        return None, 204

    @db.with_transaction
    def get(self, environment_id, resource_id_or_name, levels):
        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)
        if res_def.id != resource_id_or_name:
            from tuning_box.app import api
            url = api.url_for(
                ResourceOverrides,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=res_def.id,
            )
            return flask.redirect(url, code=308)

        level_value = hierarchy_levels.get_environment_level_value(
            environment, levels)
        res_values = db.ResourceValues.query.filter_by(
            resource_definition=res_def,
            environment=environment,
            level_value=level_value,
        ).one_or_none()
        if not res_values:
            return {}
        return res_values.overrides


class ResourceOverridesKeys(flask_restful.Resource,
                            resource_keys_operation.ResourceKeysMixin):

    def put(self, environment_id, levels, resource_id_or_name, operation):
        return self.patch(environment_id, levels,
                          resource_id_or_name, operation)

    def patch(self, environment_id, levels, resource_id_or_name, operation):
        self._do_update(environment_id, levels, resource_id_or_name,
                        operation, 'overrides')
        return None, 204
