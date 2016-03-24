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

"""Add unique constraint on component.name

Revision ID: d054eefc4c5b
Revises: ad192a40fd68
Create Date: 2016-03-25 21:34:54.487361

"""

# revision identifiers, used by Alembic.
revision = 'd054eefc4c5b'
down_revision = 'ad192a40fd68'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'component'
    with op.batch_alter_table(table_name) as batch:
        batch.create_unique_constraint(
            table_name + '_component_name_unique',
            ['name'],
        )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'component'
    with op.batch_alter_table(table_name) as batch:
        batch.drop_constraint(
            table_name + '_component_name_unique',
            type_='unique',
        )
