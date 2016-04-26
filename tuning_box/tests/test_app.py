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
from werkzeug import exceptions
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

    def test_get_components_empty(self):
        res = self.client.get('/components')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_components(self):
        self._fixture()
        res = self.client.get('/components')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [self._component_json])

    def test_get_one_component(self):
        self._fixture()
        res = self.client.get('/components/7')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, self._component_json)

    def test_get_one_component_404(self):
        res = self.client.get('/components/7')
        self.assertEqual(res.status_code, 404)

    def test_post_component(self):
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        json['name'] = 'component2'
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = 8
        json['resource_definitions'][0]['component_id'] = json['id']
        json['resource_definitions'][0]['id'] = 6
        self.assertEqual(res.json, json)
        self._assert_db_effect(db.Component, 8, app.component_fields, json)

    def test_post_component_conflict(self):
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 409)
        self._assert_not_in_db(db.Component, 8)

    def test_post_component_conflict_propagate_exc(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 409)
        self._assert_not_in_db(db.Component, 8)

    def test_post_component_no_resdef_content(self):
        self._fixture()  # Just for namespace
        json = self._component_json
        del json['id']
        del json['resource_definitions'][0]['id']
        del json['resource_definitions'][0]['component_id']
        del json['resource_definitions'][0]['content']
        json['name'] = 'component2'
        res = self.client.post('/components', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = 8
        json['resource_definitions'][0]['component_id'] = json['id']
        json['resource_definitions'][0]['id'] = 6
        json['resource_definitions'][0]['content'] = None
        self.assertEqual(res.json, json)
        self._assert_db_effect(db.Component, 8, app.component_fields, json)

    def test_delete_component(self):
        self._fixture()
        res = self.client.delete('/components/7')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        self._assert_not_in_db(db.Component, 7)

    def test_delete_component_404(self):
        res = self.client.delete('/components/7')
        self.assertEqual(res.status_code, 404)

    def test_get_environments_empty(self):
        res = self.client.get('/environments')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [])

    def test_get_environments(self):
        self._fixture()
        res = self.client.get('/environments')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, [{'id': 9, 'components': [7],
                                     'hierarchy_levels': ['lvl1', 'lvl2']}])

    def test_get_one_environment(self):
        self._fixture()
        res = self.client.get('/environments/9')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'id': 9, 'components': [7],
                                    'hierarchy_levels': ['lvl1', 'lvl2']})

    def test_get_one_environment_404(self):
        res = self.client.get('/environments/9')
        self.assertEqual(res.status_code, 404)

    def test_post_environment(self):
        self._fixture()
        json = {'components': [7], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = 10
        self.assertEqual(res.json, json)
        self._assert_db_effect(
            db.Environment, 10, app.environment_fields, json)

    def test_post_environment_preserve_id(self):
        self._fixture()
        json = {
            'id': 42,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json, json)
        self._assert_db_effect(
            db.Environment, 42, app.environment_fields, json)

    def test_post_environment_preserve_id_conflict(self):
        self._fixture()
        json = {
            'id': 9,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 409)

    def test_post_environment_preserve_id_conflict_propagate_exc(self):
        self.app.config["PROPAGATE_EXCEPTIONS"] = True
        self._fixture()
        json = {
            'id': 9,
            'components': [7],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 409)

    def test_post_environment_by_component_name(self):
        self._fixture()
        json = {
            'components': ['component1'],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 201)
        json['id'] = 10
        json['components'] = [7]
        self.assertEqual(res.json, json)
        self._assert_db_effect(
            db.Environment, 10, app.environment_fields, json)

    def test_post_environment_404(self):
        self._fixture()
        json = {'components': [8], 'hierarchy_levels': ['lvla', 'lvlb']}
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 404)
        self._assert_not_in_db(db.Environment, 10)

    def test_post_environment_by_component_name_404(self):
        self._fixture()
        json = {
            'components': ['component2'],
            'hierarchy_levels': ['lvla', 'lvlb'],
        }
        res = self.client.post('/environments', data=json)
        self.assertEqual(res.status_code, 404)
        self._assert_not_in_db(db.Environment, 10)

    def test_delete_environment(self):
        self._fixture()
        res = self.client.delete('/environments/9')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        self._assert_not_in_db(db.Environment, 9)

    def test_delete_environment_404(self):
        res = self.client.delete('/environments/9')
        self.assertEqual(res.status_code, 404)

    def test_get_environment_level_value_root(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = app.get_environment_level_value(
                db.Environment(id=9),
                [],
            )
            self.assertIsNone(level_value)

    def test_get_environment_level_value_deep(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            level_value = app.get_environment_level_value(
                db.Environment(id=9),
                [('lvl1', 'val1'), ('lvl2', 'val2')],
            )
            self.assertIsNotNone(level_value)
            self.assertEqual(level_value.level.name, 'lvl2')
            self.assertEqual(level_value.value, 'val2')
            level_value = level_value.parent
            self.assertEqual(level_value.level.name, 'lvl1')
            self.assertEqual(level_value.value, 'val1')
            self.assertIsNone(level_value.parent)

    def test_get_environment_level_value_bad_level(self):
        self._fixture()
        with self.app.app_context(), db.db.session.begin():
            exc = self.assertRaises(
                exceptions.BadRequest,
                app.get_environment_level_value,
                db.Environment(id=9),
                [('lvlx', 'val1')],
            )
            self.assertEqual(
                exc.description,
                "Unexpected level name 'lvlx'. Expected 'lvl1'.",
            )

    def test_put_resource_values_root(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'k': 'v'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNotNone(resource_values)
            self.assertEqual(resource_values.values, {'k': 'v'})
            self.assertIsNone(resource_values.level_value)

    def test_put_resource_values_deep(self):
        self._fixture()
        res = self.client.put(
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values',
            data={'k': 'v'},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNotNone(resource_values)
            self.assertEqual(resource_values.values, {'k': 'v'})
            level_value = resource_values.level_value
            self.assertEqual(level_value.level.name, 'lvl2')
            self.assertEqual(level_value.value, 'val2')
            level_value = level_value.parent
            self.assertEqual(level_value.level.name, 'lvl1')
            self.assertEqual(level_value.value, 'val1')
            self.assertIsNone(level_value.parent)

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

    def test_put_resource_values_bad_level(self):
        self._fixture()
        res = self.client.put('/environments/9/lvlx/1/resources/5/values',
                              data={'k': 'v'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.json,
            {"message": "Unexpected level name 'lvlx'. Expected 'lvl1'."},
        )
        with self.app.app_context():
            resource_values = db.ResourceValues.query.filter_by(
                environment_id=9, resource_definition_id=5).one_or_none()
            self.assertIsNone(resource_values)

    def test_get_resource_values(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {})

    def test_get_resource_values_effective(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.data, b'')
        res = self.client.get(
            '/environments/9/lvl1/1/resources/5/values?effective',
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {'key': 'value'})

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

    def test_put_resource_values_redirect(self):
        self._fixture()
        res = self.client.put(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/values',
            data={'k': 'v'},
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values',
        )

    def test_get_resource_values_redirect(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        res = self.client.get(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/values',
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values',
        )

    def test_get_resource_values_redirect_with_query(self):
        self._fixture()
        res = self.client.put('/environments/9/resources/5/values',
                              data={'key': 'value'})
        res = self.client.get(
            '/environments/9/lvl1/val1/lvl2/val2/resources/resdef1/values'
            '?effective',
        )
        self.assertEqual(res.status_code, 308)
        self.assertEqual(
            res.headers['Location'],
            'http://localhost'
            '/environments/9/lvl1/val1/lvl2/val2/resources/5/values?effective',
        )

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
