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

"""Add server_default to resource_values.values

Revision ID: 967a44dd16d5
Revises: 3b2a0f134e45
Create Date: 2016-03-25 21:12:28.939719

"""

# revision identifiers, used by Alembic.
revision = '967a44dd16d5'
down_revision = '3b2a0f134e45'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op

import tuning_box.db


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'resource_values'
    with op.batch_alter_table(table_name) as batch:
        batch.alter_column(
            'values',
            server_default='{}',
            existing_type=tuning_box.db.Json(),
        )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'resource_values'
    with op.batch_alter_table(table_name) as batch:
        batch.alter_column(
            'values',
            server_default=None,
            existing_type=tuning_box.db.Json(),
        )
