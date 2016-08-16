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

import copy

import flask
import flask_restful
from flask_restful import fields

from tuning_box import db
from tuning_box.library import resource_keys_operation

resource_definition_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'component_id': fields.Integer(default=None),
    'content': fields.Raw,
}


class ResourceDefinitionsCollection(flask_restful.Resource):
    method_decorators = [
        flask_restful.marshal_with(resource_definition_fields)
    ]

    def get(self):
        query = db.ResourceDefinition.query
        if 'component_id' in flask.request.args:
            component_id = flask.request.args.get('component_id')
            component_id = component_id or None
            query = query.filter(
                db.ResourceDefinition.component_id == component_id
            )
        return query.all()

    @db.with_transaction
    def post(self):
        data = dict()
        for field_name in resource_definition_fields.keys():
            data[field_name] = flask.request.json.get(field_name, None)
        resource_definition = db.ResourceDefinition(**data)
        db.db.session.add(resource_definition)
        return resource_definition, 201


class ResourceDefinition(flask_restful.Resource):
    method_decorators = [
        flask_restful.marshal_with(resource_definition_fields)]

    def get(self, resource_definition_id):
        return db.ResourceDefinition.query.get_or_404(resource_definition_id)

    @db.with_transaction
    def _perform_update(self, resource_definition_id):
        res_definition = db.ResourceDefinition.query.get_or_404(
            resource_definition_id)
        update_by = flask.request.json
        skip_fields = ('id', )

        for field_name in resource_definition_fields.keys():

            if field_name in skip_fields:
                continue
            if field_name in update_by:
                setattr(
                    res_definition, field_name,
                    update_by.get(field_name)
                )

    def put(self, resource_definition_id):
        return self.patch(resource_definition_id)

    def patch(self, resource_definition_id):
        self._perform_update(resource_definition_id)
        return None, 204

    @db.with_transaction
    def delete(self, resource_definition_id):
        res_definition = db.ResourceDefinition.query.get_or_404(
            resource_definition_id)
        db.db.session.delete(res_definition)
        return None, 204


class ResourceDefinitionKeys(flask_restful.Resource,
                             resource_keys_operation.KeysOperationMixin):
    method_decorators = [
        flask_restful.marshal_with(resource_definition_fields)]

    @db.with_transaction
    def _do_update(self, resource_definition_id, operation):
        res_definition = db.ResourceDefinition.query.get_or_404(
            resource_definition_id)
        content = copy.deepcopy(res_definition.content)
        self.perform_operation(operation, content,
                               flask.request.json)
        res_definition.content = content

    def put(self, resource_definition_id, operation):
        return self.patch(resource_definition_id, operation)

    def patch(self, resource_definition_id, operation):
        self._do_update(resource_definition_id, operation)
        return None, 204
