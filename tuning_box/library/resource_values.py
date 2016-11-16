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
from flask import current_app as app
import flask_restful
import six
from sqlalchemy import or_

from tuning_box import db
from tuning_box import errors
from tuning_box import library
from tuning_box.library import hierarchy_levels
from tuning_box.library import resource_keys_operation
from tuning_box.library.resource_keys_operation import KeysOperationMixin


class ResourceValues(flask_restful.Resource, KeysOperationMixin):

    KEYS_PATH_DELIMITER = '.'

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

    def _calculate_effective_values(self, result, level_value,
                                    resource_values_idx, show_lookup,
                                    lookup_path):
        level_value_id = getattr(level_value, 'id', None)
        if level_value_id in resource_values_idx:
            resource_value = resource_values_idx[level_value_id]
            if show_lookup:
                values = ((k, (v, lookup_path)) for k, v in
                          six.iteritems(resource_value.values))
                overrides = ((k, (v, lookup_path)) for k, v in
                             six.iteritems(resource_value.overrides))
            else:
                values = resource_value.values
                overrides = resource_value.overrides
            result.update(values)
            result.update(overrides)

    @db.with_transaction
    def get(self, environment_id, resource_id_or_name, levels):
        app.logger.debug("Getting resource value. Env: %s, "
                         "resource: %s, levels: %s", environment_id,
                         resource_id_or_name, levels)

        effective = 'effective' in flask.request.args
        show_lookup = 'show_lookup' in flask.request.args

        if show_lookup and not effective:
            raise errors.RequestValidationError(
                "Lookup path tracing can be done only for effective values")

        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)

        level_values = list(hierarchy_levels.iter_environment_level_values(
            environment, levels))

        level_values_ids = [l.id for l in level_values]
        app.logger.debug("Got level values ids: %s", level_values_ids)

        if effective:
            app.logger.debug("Getting effective resource value. Env: %s, "
                             "resource: %s, levels: %s", environment_id,
                             resource_id_or_name, levels)
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
            # Creating index of resource_values by level_value_id
            resource_values_idx = {r.level_value_id: r
                                   for r in resource_values}
            app.logger.debug("Resource values index size: %s",
                             len(resource_values_idx))

            result = {}
            lookup_path = '/'
            self._calculate_effective_values(
                result, None, resource_values_idx, show_lookup,
                lookup_path)

            for level_value in level_values:
                name = level_value.level.name
                value = level_value.value
                lookup_path += name + '/' + value + '/'

                self._calculate_effective_values(
                    result, level_value, resource_values_idx, show_lookup,
                    lookup_path)

            app.logger.debug("Effective values got for resource: "
                             "%s, env: %s", res_def.id, environment.id)
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
            if resource_values:
                result = resource_values.values
            else:
                result = {}
        return self._extract_keys_paths(result)

    def _extract_keys_paths(self, data):
        if 'key' not in flask.request.args:
            return data
        keys_path = flask.request.args['key'].split(self.KEYS_PATH_DELIMITER)
        result = self.do_get(data, [keys_path])
        # Single keys path is passed as GET request parameter, so we need
        # only first result
        return result[0]


class ResourceValuesKeys(flask_restful.Resource,
                         resource_keys_operation.ResourceKeysMixin):

    def put(self, environment_id, levels, resource_id_or_name, operation):
        return self.patch(environment_id, levels,
                          resource_id_or_name, operation)

    def patch(self, environment_id, levels, resource_id_or_name, operation):
        self._do_update(environment_id, levels, resource_id_or_name,
                        operation, 'values')
        return None, 204
