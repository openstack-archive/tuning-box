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
import werkzeug

import flask_restful
from flask_restful import fields

from tuning_box import db


def iter_environment_level_values(environment, levels):
    env_levels = db.EnvironmentHierarchyLevel.get_for_environment(environment)
    level_pairs = zip(env_levels, levels)
    for env_level, (level_name, level_value) in level_pairs:
        if env_level.name != level_name:
            raise werkzeug.exceptions.BadRequest(
                "Unexpected level name '{0}'. Expected '{1}'.".format(
                    level_name, env_level.name))
        level_value_db = db.get_or_create(
            db.EnvironmentHierarchyLevelValue,
            level=env_level,
            value=level_value,
        )
        yield level_value_db


def get_environment_level_value(environment, levels):
    level_value = None
    for level_value in iter_environment_level_values(environment, levels):
        pass
    return level_value


environment_hierarchy_level_fields = {
    'name': fields.String,
    'environment_id': fields.Integer,
    'parent': fields.String(attribute='parent.name')
}


class EnvironmentHierarchyLevelsCollection(flask_restful.Resource):
    method_decorators = [
        flask_restful.marshal_with(environment_hierarchy_level_fields)
    ]

    def get(self, environment_id):
        env = db.get_or_404(db.Environment, environment_id)
        return db.EnvironmentHierarchyLevel.get_for_environment(env)


class EnvironmentHierarchyLevels(flask_restful.Resource):
    method_decorators = [
        flask_restful.marshal_with(environment_hierarchy_level_fields)
    ]

    def get(self, environment_id, level):
        level = db.find_or_404(db.EnvironmentHierarchyLevel,
                               environment_id=environment_id,
                               name=level)
        return level

    @db.with_transaction
    def _do_update(self, environment_id, level):
        level = db.find_or_404(db.EnvironmentHierarchyLevel,
                               environment_id=environment_id,
                               name=level)
        level.name = flask.request.json.get('name', level.name)

    def put(self, environment_id, level):
        return self.patch(environment_id, level)

    def patch(self, environment_id, level):
        self._do_update(environment_id, level)
        return None, 204
