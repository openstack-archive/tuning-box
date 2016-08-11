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
from sqlalchemy import exc as sa_exc

from tuning_box import db
from tuning_box import errors

environment_fields = {
    'id': fields.Integer,
    'components': fields.List(fields.Integer(attribute='id')),
    'hierarchy_levels': fields.List(fields.String(attribute='name')),
}


class EnvironmentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(environment_fields)]

    def get(self):
        return db.Environment.query.all()

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
        return db.Environment.query.get_or_404(environment_id)

    # @db.with_transaction
    # def _perform_update(self, component_id):
    #     component = db.Environment.query.get_or_404(component_id)
    #     update_by = flask.request.json
    #     component.name = update_by.get('name', component.name)
    #     resource_definitions = update_by.get('resource_definitions')
    #     if resource_definitions is not None:
    #         resources = []
    #         for resource_data in resource_definitions:
    #             resource = db.ResourceDefinition.query.filter_by(
    #                 id=resource_data.get('id')
    #             ).one()
    #             resource.component_id = component.id
    #             db.db.session.add(resource)
    #             resources.append(resource)
    #         component.resource_definitions = resources
    #
    # def put(self, component_id):
    #     return self.patch(component_id)
    #
    # def patch(self, component_id):
    #     self._perform_update(component_id)
    #     return None, 204

    @db.with_transaction
    def delete(self, component_id):
        component = db.Component.query.get_or_404(component_id)
        db.db.session.delete(component)
        return None, 204

    @db.with_transaction
    def delete(self, environment_id):
        environment = db.Environment.query.get_or_404(environment_id)
        db.db.session.delete(environment)
        return None, 204
