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

from tuning_box import db


resource_definition_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'component_id': fields.Integer,
    'content': fields.Raw,
}

component_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'resource_definitions': fields.List(
        fields.Nested(resource_definition_fields)),
}


class ComponentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(component_fields)]

    def get(self):
        return db.Component.query.all()

    @db.with_transaction
    def post(self):
        component = db.Component(name=flask.request.json['name'])
        component.resource_definitions = []
        for resdef_data in flask.request.json.get('resource_definitions'):
            resdef = db.ResourceDefinition(name=resdef_data['name'],
                                           content=resdef_data.get('content'))
            component.resource_definitions.append(resdef)
        db.db.session.add(component)
        return component, 201


class Component(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(component_fields)]

    def get(self, component_id):
        return db.Component.query.get_or_404(component_id)

    @db.with_transaction
    def _perform_update(self, component_id):
        component = db.Component.query.get_or_404(component_id)
        update_by = flask.request.json
        component.name = update_by.get('name', component.name)
        resource_definintions = update_by.get('resource_definitions')
        if resource_definintions is not None:
            resources = []
            for resource_data in resource_definintions:
                resource = db.ResourceDefinition.query.filter_by(
                    id=resource_data.get('id')
                ).one()
                resource.component_id = component.id
                db.db.session.add(resource)
                resources.append(resource)
            component.resource_definitions = resources

    def put(self, component_id):
        return self.patch(component_id)

    def patch(self, component_id):
        self._perform_update(component_id)
        return None, 204

    @db.with_transaction
    def delete(self, component_id):
        component = db.Component.query.get_or_404(component_id)
        db.db.session.delete(component)
        return None, 204
