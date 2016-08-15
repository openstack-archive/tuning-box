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


class BaseTest(base.TestCase):

    def setUp(self):
        super(BaseTest, self).setUp()
        self.app = app.build_app(configure_logging=False,
                                 with_keystone=False)
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

    def _assert_db_effect(self, model, key, fields, expected):
        with self.app.app_context():
            obj = model.query.get(key)
            self.assertIsNotNone(obj)
            marshalled = flask_restful.marshal(obj, fields)
        self.assertItemsEqual(expected, marshalled)

    def _assert_not_in_db(self, model, key):
        with self.app.app_context():
            obj = model.query.get(key)
            self.assertIsNone(obj)


class TestApp(BaseTest):
    def test_put_resource_values_overrides_root(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/overrides',
                              data={'k': 'v'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNotNone(resource_values)
            self.assertEqual(resource_values.overrides, {'k': 'v'})
            self.assertIsNone(resource_values.level_value)

    def test_put_resource_values_overrides_deep(self):
        self._fixture()
        res = self.client.put(
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/overrides',
            data={'k': 'v'},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNotNone(resource_values)
            self.assertEqual(resource_values.overrides, {'k': 'v'})
            level_value = resource_values.level_value
            self.assertEqual(level_value.level.name, 'lvl2')
            self.assertEqual(level_value.value, 'val2')
            level_value = level_value.parent
            self.assertEqual(level_value.level.name, 'lvl1')
            self.assertEqual(level_value.value, 'val1')
            self.assertIsNone(level_value.parent)

    def test_get_resource_values_local_override(self):
        self._fixture()
        res = self.client.put('/environments/9/lvl1/1/resources/5/values',
                              data={'key': 'value1'})
        res = self.client.put('/environments/9/lvl1/1/resources/5/overrides',
                              data={'key': 'value2'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values?effective',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'key': 'value2'})

    def test_get_resource_values_level_override(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value', 'key1': 'value'})
        res = self.client.put('/environments/9/lvl1/1/resources/5/values',
                              data={'key': 'value1'})
        res = self.client.put('/environments/9/lvl1/2/resources/5/values',
                              data={'key1': 'value2'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values?effective',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'key': 'value1', 'key1': 'value'})

    def test_get_resource_values_level_and_local_override(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value', 'key1': 'value'})
        res = self.client.put('/environments/9/lvl1/1/resources/5/values',
                              data={'key': 'value1'})
        res = self.client.put('/environments/9/lvl1/1/resources/5/overrides',
                              data={'key1': 'value2'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values?effective',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'key': 'value1', 'key1': 'value2'})

    def test_put_resource_overrides_redirect(self):
        self._fixture()
        res = self.client.put(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/overrides',
            data={'k': 'v'},
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/overrides',
        )

    def test_get_resource_overrides_redirect(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/overrides',
                              data={'key': 'value'})
        res = self.client.get(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/overrides',
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/overrides',
        )


class TestAppPrefixed(base.PrefixedTestCaseMixin, TestApp):
    pass
