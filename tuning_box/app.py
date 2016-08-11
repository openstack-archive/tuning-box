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
from sqlalchemy import exc as sa_exc
from werkzeug import exceptions

from tuning_box import converters
from tuning_box import db
from tuning_box import errors
from tuning_box.library import components
from tuning_box.library import environments
from tuning_box import logger
from tuning_box.middleware import keystone

# These handlers work if PROPAGATE_EXCEPTIONS is off (non-Nailgun case)
api_errors = {
    'IntegrityError': {'status': 409},  # sqlalchemy IntegrityError
    'TuningboxIntegrityError': {'status': 409},  # sqlalchemy IntegrityError
}
api = flask_restful.Api(errors=api_errors)

api.add_resource(components.ComponentsCollection, '/components')
api.add_resource(components.Component, '/components/<int:component_id>')
api.add_resource(environments.EnvironmentsCollection, '/environments')
api.add_resource(environments.Environment,
                 '/environments/<int:environment_id>')


def with_transaction(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        with db.db.session.begin():
            return f(*args, **kwargs)

    return inner


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


def handle_integrity_error_(exc):
    response = flask.jsonify(msg=exc.args[0])
    response.status_code = 409
    return response


def build_app(configure_logging=True, with_keystone=True):
    app = flask.Flask(__name__)
    app.url_map.converters.update(converters.ALL)
    api.init_app(app)  # init_app spoils Api object if app is a blueprint
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # silence warning
    # TUNINGBOX_SETTINGS is the path to the file with tuning_box configuration
    app.config.from_envvar('TUNINGBOX_SETTINGS', silent=True)
    # These handlers work if PROPAGATE_EXCEPTIONS is on (Nailgun case)
    app.register_error_handler(sa_exc.IntegrityError, handle_integrity_error)
    app.register_error_handler(errors.TuningboxIntegrityError, handle_integrity_error_)
    db.db.init_app(app)
    if configure_logging:
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        logger.init_logger(log_level)
    if with_keystone:
        app.wsgi_app = keystone.KeystoneMiddleware(app)
    return app


def main():
    import logging
    logging.basicConfig(level=logging.DEBUG)

    app = build_app()
    app.run()

if __name__ == '__main__':
    main()
