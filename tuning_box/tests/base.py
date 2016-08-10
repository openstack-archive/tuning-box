# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
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

from alembic import command as alembic_command
from oslotest import base

from tuning_box import db
from tuning_box import migration


class TestCase(base.BaseTestCase):

    """Test case base class for all unit tests."""

    DB_URI = 'postgresql://openstack_citest:openstack_citest' \
             '@localhost/postgres'

    def _save_delete_records(self, model):
        if db.db.engine.dialect.has_table(db.db.engine, model.__table__.name):
            model.query.delete()

    def _clean_db(self):
        self._save_delete_records(db.ResourceValues)
        self._save_delete_records(db.ResourceDefinition)
        self._save_delete_records(db.Component)
        self._save_delete_records(db.EnvironmentHierarchyLevelValue)
        self._save_delete_records(db.EnvironmentHierarchyLevel)
        self._save_delete_records(db.Environment)
        config = migration.get_alembic_config(db.db.engine)
        alembic_command.downgrade(config, 'base')
        alembic_command.upgrade(config, 'head')

    def get_alembic_config(self, engine):
        return migration.get_alembic_config(engine)


class PrefixedTestCaseMixin(object):
    def setUp(self):
        db.prefix_tables(db, 'test_prefix_')
        self.addCleanup(db.unprefix_tables, db)
        super(PrefixedTestCaseMixin, self).setUp()
