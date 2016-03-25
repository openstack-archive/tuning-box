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

"""Add overrides to resource_values

Revision ID: ad192a40fd68
Revises: 967a44dd16d5
Create Date: 2016-03-25 21:26:19.170101

"""

# revision identifiers, used by Alembic.
revision = 'ad192a40fd68'
down_revision = '967a44dd16d5'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op
import sqlalchemy as sa

import tuning_box.db


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    op.add_column(table_prefix + 'resource_values', sa.Column(
        'overrides',
        tuning_box.db.Json(),
        server_default='{}',
        nullable=True,
    ))


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    op.drop_column(table_prefix + 'resource_values', 'overrides')
