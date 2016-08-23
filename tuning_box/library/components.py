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
from tuning_box import library
from tuning_box.library import resource_definitions

component_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'resource_definitions': fields.List(fields.Nested(
        resource_definitions.resource_definition_fields
    ))
}


class ComponentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(component_fields)]

    def get(self):
        return db.Component.query.order_by(db.Component.id).all()

    @db.with_transaction
    def post(self):
        component = db.Component(name=flask.request.json['name'])
        component.resource_definitions = []
        for res_def_data in flask.request.json.get('resource_definitions', []):
            res_def = db.ResourceDefinition(
                name=res_def_data['name'], content=res_def_data.get('content'))
            component.resource_definitions.append(res_def)
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
        res_definitions = update_by.get('resource_definitions')
        if res_definitions is not None:
            ids = [data['id'] for data in res_definitions]
            resources = library.load_objects(db.ResourceDefinition, ids)
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
