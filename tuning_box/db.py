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
import json
import re

import flask
import flask_sqlalchemy
import sqlalchemy.event
import sqlalchemy.ext.declarative as sa_decl
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy import types

try:
    from importlib import reload
except ImportError:
    pass  # in 2.x reload is builtin

db = flask_sqlalchemy.SQLAlchemy(session_options={'autocommit': True})
pk_type = db.Integer
pk = functools.partial(db.Column, pk_type, primary_key=True)


def fk(cls, **kwargs):
    return db.Column(pk_type, db.ForeignKey(cls.id), **kwargs)


class BaseQuery(flask_sqlalchemy.BaseQuery):
    def get_by_id_or_name(self, id_or_name):
        if isinstance(id_or_name, int):
            result = self.get(id_or_name)
        else:
            result = self.filter_by(name=id_or_name).one_or_none()
        if result is None:
            flask.abort(404)
        return result

    # one_or_none is not present in sqlalchemy < 1.0.9
    def one_or_none(self):
        ret = list(self)
        l = len(ret)
        if l == 1:
            return ret[0]
        elif l == 0:
            return None
        else:
            raise orm_exc.MultipleResultsFound(
                "Multiple rows were found for one_or_none()")


def _tablename(cls_name):
    def repl(match):
        res = match.group().lower()
        if match.start():
            res = "_" + res
        return res

    return ModelMixin.table_prefix + re.sub("[A-Z]", repl, cls_name)


class ModelMixin(object):
    query_class = BaseQuery
    id = db.Column(pk_type, primary_key=True)

    try:
        table_prefix = ModelMixin.table_prefix  # keep prefix during reload
    except NameError:
        table_prefix = ""  # first import, not reload

    @sa_decl.declared_attr
    def __tablename__(cls):
        return _tablename(cls.__name__)

    def __repr__(self):
        args = []
        for attr in self.__repr_attrs__:
            value = getattr(self, attr)
            if attr == 'content' and value is not None and len(value) > 15:
                value = value[:10] + '<...>'
            args.append('{}={!r}'.format(attr, value))
        return '{}({})'.format(type(self).__name__, ','.join(args))


class Json(types.TypeDecorator):
    impl = db.Text

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)


# Component registry


class Component(ModelMixin, db.Model):
    name = db.Column(db.String(128), unique=True)

    __repr_attrs__ = ('id', 'name')


class ResourceDefinition(ModelMixin, db.Model):
    name = db.Column(db.String(128))
    component_id = fk(Component)
    component = db.relationship(Component, backref='resource_definitions')
    content = db.Column(Json)

    __repr_attrs__ = ('id', 'name', 'component', 'content')

# Environment data storage


class Environment(ModelMixin, db.Model):
    @sa_decl.declared_attr
    def environment_components_table(cls):
        return db.Table(
            _tablename('environment_components'),
            db.Column('environment_id', pk_type, db.ForeignKey(cls.id)),
            db.Column('component_id', pk_type, db.ForeignKey(Component.id)),
        )

    @sa_decl.declared_attr
    def components(cls):
        return db.relationship(
            Component, secondary=cls.environment_components_table)

    __repr_attrs__ = ('id',)


class EnvironmentHierarchyLevel(ModelMixin, db.Model):
    environment_id = fk(Environment)
    environment = db.relationship(Environment, backref='hierarchy_levels')
    name = db.Column(db.String(128))

    @sa_decl.declared_attr
    def parent_id(cls):
        return db.Column(pk_type, db.ForeignKey(cls.id))

    @sa_decl.declared_attr
    def parent(cls):
        return db.relationship(cls,
                               backref=db.backref('child', uselist=False),
                               remote_side=cls.id)

    __table_args__ = (
        db.UniqueConstraint('environment_id', 'name'),
        db.UniqueConstraint('environment_id', 'parent_id'),
    )
    __repr_attrs__ = ('id', 'environment', 'parent', 'name')

    @classmethod
    def get_for_environment(cls, environment):
        query = cls.query.filter_by(environment=environment, parent=None)
        root_level = query.one_or_none()
        if not root_level:
            return []
        env_levels = [root_level]
        while env_levels[-1].child:
            env_levels.append(env_levels[-1].child)
        return env_levels


class EnvironmentHierarchyLevelValue(ModelMixin, db.Model):
    level_id = fk(EnvironmentHierarchyLevel)
    level = db.relationship(EnvironmentHierarchyLevel)
    value = db.Column(db.String(128))

    @sa_decl.declared_attr
    def parent_id(cls):
        return db.Column(pk_type, db.ForeignKey(cls.id))

    @sa_decl.declared_attr
    def parent(cls):
        return db.relationship(cls, remote_side=cls.id)

    # TODO(yorik-sar): add UniqueConstraint for all fields
    __repr_attrs__ = ('id', 'level', 'parent', 'value')


class ResourceValues(ModelMixin, db.Model):
    environment_id = fk(Environment)
    environment = db.relationship(Environment)
    resource_definition_id = fk(ResourceDefinition)
    resource_definition = db.relationship(ResourceDefinition)
    level_value_id = fk(EnvironmentHierarchyLevelValue)
    level_value = db.relationship('EnvironmentHierarchyLevelValue')
    values = db.Column(Json, server_default='{}')
    overrides = db.Column(Json, server_default='{}')

    __table_args__ = (
        db.UniqueConstraint(environment_id, resource_definition_id,
                            level_value_id),
    )
    __repr_attrs__ = ('id', 'environment', 'resource_definition',
                      'level_value', 'values')


def get_or_create(cls, **attrs):
    with db.session.begin(nested=True):
        item = cls.query.filter_by(**attrs).one_or_none()
        if not item:
            item = cls(**attrs)
            db.session.add(item)
            # TODO(yorik-sar): handle constraints failure in case of
            # race condition
    return item


def fix_sqlite():
    engine = db.engine

    @sqlalchemy.event.listens_for(engine, "connect")
    def _connect(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    @sqlalchemy.event.listens_for(engine, "begin")
    def _begin(conn):
        conn.execute("BEGIN")


def prefix_tables(module, prefix):
    ModelMixin.table_prefix = prefix
    reload(module)


def unprefix_tables(module):
    ModelMixin.table_prefix = ""
    reload(module)
