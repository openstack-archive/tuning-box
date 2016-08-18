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

"""Remove hierarchy for level values

Revision ID: a86472389a70
Revises: 0c586adad733
Create Date: 2016-08-18 14:00:03.197693

"""

# revision identifiers, used by Alembic.
revision = 'a86472389a70'
down_revision = '0c586adad733'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op
import sqlalchemy as sa


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'environment_hierarchy_level_value'
    with op.batch_alter_table(table_name) as batch:
        batch.drop_column('parent_id')

        batch.drop_constraint(
            table_name + '_level_id_fkey',
            type_='foreignkey'
        )
        batch.create_foreign_key(
            table_name + '_level_id_fkey',
            table_prefix + 'environment_hierarchy_level',
            ['level_id'], ['id'], ondelete='CASCADE'
        )

        batch.create_unique_constraint(
            table_name + '_level_id_value_unique',
            ['level_id', 'value']
        )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'environment_hierarchy_level_value'
    with op.batch_alter_table(table_name) as batch:
        batch.drop_constraint(
            table_name + '_level_id_value_unique',
            type_='unique'
        )

        batch.drop_constraint(
            table_name + '_level_id_fkey',
            type_='foreignkey'
        )
        batch.create_foreign_key(
            table_name + '_level_id_fkey',
            table_prefix + 'environment_hierarchy_level',
            ['level_id'], ['id']
        )

        batch.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch.create_foreign_key(
            table_name + '_parent_id_fkey',
            table_name,
            ['parent_id'], ['id']
        )
