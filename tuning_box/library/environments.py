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
from flask_restful import fields

from tuning_box import db
from tuning_box import errors
from tuning_box import library

environment_fields = {
    'id': fields.Integer,
    'components': fields.List(fields.Integer(attribute='id')),
    'hierarchy_levels': fields.List(fields.String(attribute='name')),
}


class EnvironmentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(environment_fields)]

    def get(self):
        envs = db.Environment.query.order_by(db.Environment.id).all()
        result = []
        for env in envs:
            hierarchy_levels = db.EnvironmentHierarchyLevel.\
                get_for_environment(env)
            # Proper order of levels can't be provided by ORM backref
            result.append({'id': env.id, 'components': env.components,
                           'hierarchy_levels': hierarchy_levels})
        return result, 200

    def _check_components(self, components):
        identities = set()
        duplicates = set()
        id_names = ('id', 'name')
        for component in components:
            for id_name in id_names:
                value = getattr(component, id_name)

                if value not in identities:
                    identities.add(value)
                else:
                    duplicates.add(value)
        if duplicates:
            raise errors.TuningboxIntegrityError(
                "Components duplicates: {0}".format(duplicates))

    @db.with_transaction
    def post(self):
        component_ids = flask.request.json['components']
        components = [db.Component.query.get_by_id_or_name(i)
                      for i in component_ids]
        self._check_components(components)

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
        env = db.Environment.query.get_or_404(environment_id)
        hierarchy_levels = db.EnvironmentHierarchyLevel.\
            get_for_environment(env)
        # Proper order of levels can't be provided by ORM backref
        return {'id': env.id, 'components': env.components,
                'hierarchy_levels': hierarchy_levels}, 200

    def _update_components(self, environment, components):
        if components is not None:
            new_components = library.load_objects_by_id_or_name(
                db.Component, components)
            environment.components = new_components

    def _update_hierarchy_levels(self, environment, hierarchy_levels_names):
        if hierarchy_levels_names is not None:
            old_hierarchy_levels = db.EnvironmentHierarchyLevel.query.filter(
                db.EnvironmentHierarchyLevel.environment_id == environment.id
            ).all()

            new_hierarchy_levels = []

            for level_name in hierarchy_levels_names:
                level = db.get_or_create(
                    db.EnvironmentHierarchyLevel,
                    name=level_name,
                    environment=environment
                )
                new_hierarchy_levels.append(level)

            parent_id = None
            for level in new_hierarchy_levels:
                level.parent_id = parent_id
                parent_id = level.id
            for old_level in old_hierarchy_levels:
                if old_level not in new_hierarchy_levels:
                    db.db.session.delete(old_level)
            environment.hierarchy_levels = new_hierarchy_levels

    @db.with_transaction
    def _perform_update(self, environment_id):
        environment = db.Environment.query.get_or_404(environment_id)
        update_by = flask.request.json

        components = update_by.get('components')
        self._update_components(environment, components)

        hierarchy_levels = update_by.get('hierarchy_levels')
        self._update_hierarchy_levels(environment, hierarchy_levels)

    def put(self, environment_id):
        return self.patch(environment_id)

    def patch(self, environment_id):
        self._perform_update(environment_id)
        return None, 204

    @db.with_transaction
    def delete(self, environment_id):
        environment = db.Environment.query.get_or_404(environment_id)
        db.db.session.delete(environment)
        return None, 204
