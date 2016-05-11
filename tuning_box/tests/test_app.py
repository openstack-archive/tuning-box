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

import json

from flask import testing
import flask_restful
from werkzeug import wrappers

from tuning_box import app
from tuning_box import db
from tuning_box.tests import base


class JSONResponse(wrappers.BaseResponse):
    @property
    def json(self):
        return json.loads(self.data.decode(self.charset))


class Client(testing.FlaskClient):
    def __init__(self, app):
        super(Client, self).__init__(app, response_wrapper=JSONResponse)

    def open(self, *args, **kwargs):
        data = kwargs.get('data')
        if data is not None:
            kwargs['data'] = json.dumps(data)
            kwargs['content_type'] = 'application/json'
        return super(Client, self).open(*args, **kwargs)


class TestApp(base.TestCase):
    def setUp(self):
        super(TestApp, self).setUp()
        self.app = app.build_app()
        self.app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///'
        with self.app.app_context():
            db.fix_sqlite()
            db.db.create_all()
        self.client = Client(self.app)

    def _fixture(self):
        with self.app.app_context(), db.db.session.begin():
            component = db.Component(
                id=7,
                name='component1',
                resource_definitions=[db.ResourceDefinition(
                    id=5,
                    name='resdef1',
                    content={'key': 'nsname.key'},
                )],
            )
            db.db.session.add(component)
            environment = db.Environment(id=9, components=[component])
            hierarchy_levels = [
                db.EnvironmentHierarchyLevel(name="lvl1"),
                db.EnvironmentHierarchyLevel(name="lvl2"),
            ]
            hierarchy_levels[1].parent = hierarchy_levels[0]
            environment.hierarchy_levels = hierarchy_levels
            db.db.session.add(environment)

    @property
    def _component_json(self):
        return {
            'id': 7,
            'name': 'component1',
            'resource_definitions': [{
                'id': 5,
                'name': 'resdef1',
                'component_id': 7,
                'content': {'key': 'nsname.key'},
            }],
        }

    def _assert_db_effect(self, model, key, fields, expected):
        with self.app.app_context():
            obj = model.query.get(key)
            self.assertIsNotNone(obj)
            marshalled = flask_restful.marshal(obj, fields)
        self.assertEqual(expected, marshalled)

    def _assert_not_in_db(self, model, key):
        with self.app.app_context():
            obj = model.query.get(key)
            self.assertIsNone(obj)


class TestAppPrefixed(base.PrefixedTestCaseMixin, TestApp):
    pass
