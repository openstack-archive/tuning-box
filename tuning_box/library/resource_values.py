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

import flask
from flask import current_app as app
import flask_restful
from sqlalchemy import or_

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
        app.logger.debug("Getting resource value. Env: %s, "
                         "resource: %s, levels: %s", environment_id,
                         resource_id_or_name, levels)
        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)

        level_values = list(hierarchy_levels.iter_environment_level_values(
            environment, levels))

        level_values_ids = [l.id for l in level_values]
        app.logger.debug("Got level values ids: %s", level_values_ids)

        if 'effective' in flask.request.args:
            app.logger.debug("Getting effective resource value. Env: %s, "
                             "resource: %s, levels: %s", environment_id,
                             resource_id_or_name, levels)
            show_lookup = 'show_lookup' in flask.request.args
            resource_values = db.ResourceValues.query.filter(
                or_(
                    db.ResourceValues.level_value_id.in_(level_values_ids),
                    db.ResourceValues.level_value_id.is_(None)
                ),
                db.ResourceValues.resource_definition == res_def,
                db.ResourceValues.environment == environment
            ).all()
            app.logger.debug("Processing values for resource: %s, env: %s. "
                             "Loaded resource values: %s",
                             res_def.id, environment.id, len(resource_values))
            result = {}
            lookup_path = ''

            # Creating index of resource_values by level_value_id
            resource_values_idx = {}
            for res_value in resource_values:
                resource_values_idx[res_value.level_value_id] = res_value
            app.logger.debug("Resource values index size: %s",
                             len(resource_values_idx))

            for level_value in itertools.chain([None], level_values):
                if level_value is not None:
                    level_value_id = level_value.id
                    name = level_value.level.name
                    value = level_value.value
                    lookup_path += name + '/' + value + '/'
                else:
                    level_value_id = None
                    lookup_path += '/'

                if level_value_id in resource_values_idx:
                    resource_value = resource_values_idx[level_value_id]
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
            app.logger.debug("Effective values got for resource: "
                             "%s, env: %s", res_def.id, environment.id)
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
            app.logger.debug("Values got for resource: "
                             "%s, env: %s", res_def.id, environment.id)
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
