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

# These handlers work if PROPAGATE_EXCEPTIONS is off (non-Nailgun case)
api_errors = {
    'IntegrityError': {'status': 409},  # sqlalchemy IntegrityError
}
api = flask_restful.Api(errors=api_errors)

from tuning_box.resources import components
from tuning_box.resources import environments
from tuning_box.resources import resources

# Adding resources
api.add_resource(components.ComponentsCollection, '/components')
api.add_resource(components.Component, '/components/<int:component_id>')
api.add_resource(environments.EnvironmentsCollection, '/environments')
api.add_resource(environments.Environment,
                 '/environments/<int:environment_id>')
api.add_resource(
    resources.ResourceValues, '/environments/<int:environment_id>'
                              '/<levels:levels>resources'
                              '/<id_or_name:resource_id_or_name>/values')
api.add_resource(
    resources.ResourceOverrides, '/environments/<int:environment_id>'
                                 '/<levels:levels>resources'
                                 '/<id_or_name:resource_id_or_name>/overrides')


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
