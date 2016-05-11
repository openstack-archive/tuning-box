#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import flask
import flask_restful
from flask_restful import fields
from werkzeug import exceptions

from tuning_box import db


environment_fields = {
    'id': fields.Integer,
    'components': fields.List(fields.Integer(attribute='id')),
    'hierarchy_levels': fields.List(fields.String(attribute='name')),
}


class EnvironmentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(environment_fields)]

    def get(self):
        return db.Environment.query.all()

    @db.with_transaction
    def post(self):
        component_ids = flask.request.json['components']
        # TODO(yorik-sar): verify that resource names do not clash
        components = [db.Component.query.get_by_id_or_name(i)
                      for i in component_ids]

        hierarchy_levels = []
        level = None
        for name in flask.request.json['hierarchy_levels']:
            level = db.EnvironmentHierarchyLevel(name=name, parent=level)
            hierarchy_levels.append(level)

        environment = db.Environment(components=components,
                                     hierarchy_levels=hierarchy_levels)
        if 'id' in flask.request.json:
            environment.id = flask.request.json['id']
        db.db.session.add(environment)
        return environment, 201


class Environment(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(environment_fields)]

    def get(self, environment_id):
        return db.Environment.query.get_or_404(environment_id)

    @db.with_transaction
    def delete(self, environment_id):
        environment = db.Environment.query.get_or_404(environment_id)
        db.db.session.delete(environment)
        return None, 204


def iter_environment_level_values(environment, levels):
    env_levels = db.EnvironmentHierarchyLevel.get_for_environment(environment)
    level_pairs = zip(env_levels, levels)
    parent_level_value = None
    for env_level, (level_name, level_value) in level_pairs:
        if env_level.name != level_name:
            raise exceptions.BadRequest(
                "Unexpected level name '%s'. Expected '%s'." % (
                    level_name, env_level.name))
        level_value_db = db.get_or_create(
            db.EnvironmentHierarchyLevelValue,
            level=env_level,
            parent=parent_level_value,
            value=level_value,
        )
        yield level_value_db
        parent_level_value = level_value_db


def get_environment_level_value(environment, levels):
    level_value = None
    for level_value in iter_environment_level_values(environment, levels):
        pass
    return level_value
