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
from alembic import config as alembic_config

import tuning_box
from tuning_box import app
from tuning_box import db


def get_alembic_config(engine):
    config = alembic_config.Config()
    config.set_main_option('sqlalchemy.url', str(engine.url))
    config.set_main_option(
        'script_location', tuning_box.get_migrations_dir())
    config.set_main_option('version_table', 'alembic_version')
    return config


def upgrade():
    with app.build_app(with_keystone=False).app_context():
        config = get_alembic_config(db.db.engine)
        alembic_command.upgrade(config, 'head')


def downgrade():
    with app.build_app(with_keystone=False).app_context():
        config = get_alembic_config(db.db.engine)
        alembic_command.downgrade(config, 'base')
