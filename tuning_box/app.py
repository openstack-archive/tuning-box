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

import functools
import itertools

import flask
import flask_restful
from flask_restful import fields
from sqlalchemy import exc as sa_exc
from werkzeug import exceptions

from tuning_box import converters
from tuning_box import db

# These handlers work if PROPAGATE_EXCEPTIONS is off (non-Nailgun case)
api_errors = {
    'IntegrityError': {'status': 409},  # sqlalchemy IntegrityError
}
api = flask_restful.Api(errors=api_errors)

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


def with_transaction(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        with db.db.session.begin():
            return f(*args, **kwargs)

    return inner


@api.resource('/components')
class ComponentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(component_fields)]

    def get(self):
        return db.Component.query.all()

    @with_transaction
    def post(self):
        component = db.Component(name=flask.request.json['name'])
        component.resource_definitions = []
        for resdef_data in flask.request.json.get('resource_definitions'):
            resdef = db.ResourceDefinition(name=resdef_data['name'],
                                           content=resdef_data.get('content'))
            component.resource_definitions.append(resdef)
        db.db.session.add(component)
        return component, 201


@api.resource('/components/<int:component_id>')
class Component(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(component_fields)]

    def get(self, component_id):
        return db.Component.query.get_or_404(component_id)

    @with_transaction
    def delete(self, component_id):
        component = db.Component.query.get_or_404(component_id)
        db.db.session.delete(component)
        return None, 204

environment_fields = {
    'id': fields.Integer,
    'components': fields.List(fields.Integer(attribute='id')),
    'hierarchy_levels': fields.List(fields.String(attribute='name')),
}


@api.resource('/environments')
class EnvironmentsCollection(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(environment_fields)]

    def get(self):
        return db.Environment.query.all()

    @with_transaction
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


@api.resource('/environments/<int:environment_id>')
class Environment(flask_restful.Resource):
    method_decorators = [flask_restful.marshal_with(environment_fields)]

    def get(self, environment_id):
        return db.Environment.query.get_or_404(environment_id)

    @with_transaction
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


@api.resource(
    '/environments/<int:environment_id>' +
    '/<levels:levels>resources/<id_or_name:resource_id_or_name>/values')
class ResourceValues(flask_restful.Resource):
    @with_transaction
    def put(self, environment_id, levels, resource_id_or_name):
        environment = db.Environment.query.get_or_404(environment_id)
        level_value = get_environment_level_value(environment, levels)
        # TODO(yorik-sar): filter by environment
        resdef = db.ResourceDefinition.query.get_by_id_or_name(
            resource_id_or_name)
        if resdef.id != resource_id_or_name:
            return flask.redirect(api.url_for(
                ResourceValues,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=resdef.id,
            ), code=308)
        esv = db.get_or_create(
            db.ResourceValues,
            environment=environment,
            resource_definition=resdef,
            level_value=level_value,
        )
        esv.values = flask.request.json
        return None, 204

    @with_transaction
    def get(self, environment_id, resource_id_or_name, levels):
        environment = db.Environment.query.get_or_404(environment_id)
        level_values = list(iter_environment_level_values(environment, levels))
        # TODO(yorik-sar): filter by environment
        resdef = db.ResourceDefinition.query.get_by_id_or_name(
            resource_id_or_name)
        if resdef.id != resource_id_or_name:
            url = api.url_for(
                ResourceValues,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=resdef.id,
            )
            if flask.request.query_string:
                qs = flask.request.query_string.decode('utf-8')
                url += '?' + qs
            return flask.redirect(url, code=308)
        if 'effective' in flask.request.args:
            resource_values = db.ResourceValues.query.filter_by(
                resource_definition=resdef,
                environment=environment,
            ).all()
            result = {}
            for level_value in itertools.chain([None], level_values):
                for resource_value in resource_values:
                    if resource_value.level_value == level_value:
                        result.update(resource_value.values)
                        result.update(resource_value.overrides)
                        break
            return result
        else:
            if not level_values:
                level_value = None
            else:
                level_value = level_values[-1]
            resource_values = db.ResourceValues.query.filter_by(
                resource_definition=resdef,
                environment=environment,
                level_value=level_value,
            ).one_or_none()
            if not resource_values:
                return {}
            return resource_values.values


@api.resource(
    '/environments/<int:environment_id>' +
    '/<levels:levels>resources/<id_or_name:resource_id_or_name>/overrides')
class ResourceOverrides(flask_restful.Resource):
    @with_transaction
    def put(self, environment_id, levels, resource_id_or_name):
        environment = db.Environment.query.get_or_404(environment_id)
        level_value = get_environment_level_value(environment, levels)
        # TODO(yorik-sar): filter by environment
        resdef = db.ResourceDefinition.query.get_by_id_or_name(
            resource_id_or_name)
        if resdef.id != resource_id_or_name:
            return flask.redirect(api.url_for(
                ResourceOverrides,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=resdef.id,
            ), code=308)
        esv = db.get_or_create(
            db.ResourceValues,
            environment=environment,
            resource_definition=resdef,
            level_value=level_value,
        )
        esv.overrides = flask.request.json
        return None, 204

    @with_transaction
    def get(self, environment_id, resource_id_or_name, levels):
        environment = db.Environment.query.get_or_404(environment_id)
        level_value = get_environment_level_value(environment, levels)
        # TODO(yorik-sar): filter by environment
        resdef = db.ResourceDefinition.query.get_by_id_or_name(
            resource_id_or_name)
        if resdef.id != resource_id_or_name:
            url = api.url_for(
                ResourceOverrides,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=resdef.id,
            )
            return flask.redirect(url, code=308)
        resource_values = db.ResourceValues.query.filter_by(
            resource_definition=resdef,
            environment=environment,
            level_value=level_value,
        ).one_or_none()
        if not resource_values:
            return {}
        return resource_values.overrides


def handle_integrity_error(exc):
    response = flask.jsonify(msg=exc.args[0])
    response.status_code = 409
    return response


def build_app():
    app = flask.Flask(__name__)
    app.url_map.converters.update(converters.ALL)
    api.init_app(app)  # init_app spoils Api object if app is a blueprint
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # silence warning
    # These handlers work if PROPAGATE_EXCEPTIONS is on (Nailgun case)
    app.register_error_handler(sa_exc.IntegrityError, handle_integrity_error)
    db.db.init_app(app)
    return app


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    app = build_app()
    app.run()

if __name__ == '__main__':
    main()
