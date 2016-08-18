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
from sqlalchemy import exc as sa_exc

from tuning_box import converters
from tuning_box import db
from tuning_box import errors
from tuning_box.library import components
from tuning_box.library import environments
from tuning_box.library import hierarchy_levels
from tuning_box.library import resource_definitions
from tuning_box.library import resource_overrides
from tuning_box.library import resource_values
from tuning_box import logger
from tuning_box.middleware import keystone

# These handlers work if PROPAGATE_EXCEPTIONS is off (non-Nailgun case)
api_errors = {
    'IntegrityError': {'status': 409},  # sqlalchemy IntegrityError
    'TuningboxIntegrityError': {'status': 409},
    'KeysOperationError': {'status': 409},
    'TuningboxNotFound': {'status': 404}
}
api = flask_restful.Api(errors=api_errors)

# Components
api.add_resource(components.ComponentsCollection, '/components')
api.add_resource(components.Component, '/components/<int:component_id>')

# Resource definitions
api.add_resource(
    resource_definitions.ResourceDefinitionsCollection,
    '/resource_definitions',
)
api.add_resource(
    resource_definitions.ResourceDefinition,
    '/resource_definition/<int:resource_definition_id>'
)
api.add_resource(
    resource_definitions.ResourceDefinitionKeys,
    '/resource_definition/<int:resource_definition_id>/'
    'keys/<keys_operation:operation>'
)

# Resource values
api.add_resource(
    resource_values.ResourceValues,
    '/environments/<int:environment_id>/<levels:levels>resources/'
    '<id_or_name:resource_id_or_name>/values'
)
api.add_resource(
    resource_values.ResourceValuesKeys,
    '/environments/<int:environment_id>/<levels:levels>resources/'
    '<id_or_name:resource_id_or_name>/values/'
    'keys/<keys_operation:operation>'
)

# Resource overrides
api.add_resource(
    resource_overrides.ResourceOverrides,
    '/environments/<int:environment_id>/'
    '<levels:levels>resources/<id_or_name:resource_id_or_name>/overrides'
)
api.add_resource(
    resource_overrides.ResourceOverridesKeys,
    '/environments/<int:environment_id>/'
    '<levels:levels>resources/<id_or_name:resource_id_or_name>/overrides/'
    'keys/<keys_operation:operation>'
)

# Environments
api.add_resource(environments.EnvironmentsCollection, '/environments')
api.add_resource(
    environments.Environment,
    '/environments/<int:environment_id>',  # Backward compatibility support
    '/environment/<int:environment_id>'
)

# Hierarchy levels
api.add_resource(
    hierarchy_levels.EnvironmentHierarchyLevelsCollection,
    '/environments/<int:environment_id>/hierarchy_levels'
)
api.add_resource(
    hierarchy_levels.EnvironmentHierarchyLevels,
    '/environments/<int:environment_id>/hierarchy_levels/'
    '<string:level>'
)


def handle_integrity_error(exc):
    response = flask.jsonify(msg=exc.args[0])
    response.status_code = 409
    return response


def handle_object_not_found(exc):
    response = flask.jsonify(msg=exc.args[0])
    response.status_code = 404
    return response


def handle_keys_operation_error(exc):
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
    app.register_error_handler(errors.TuningboxIntegrityError,
                               handle_integrity_error)
    app.register_error_handler(errors.TuningboxNotFound,
                               handle_object_not_found)
    app.register_error_handler(errors.KeysOperationError,
                               handle_keys_operation_error)
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
