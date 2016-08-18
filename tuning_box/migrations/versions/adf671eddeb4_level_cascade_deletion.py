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

"""Level cascade deletion on environment removal

Revision ID: adf671eddeb4
Revises: a86472389a70
Create Date: 2016-08-19 16:39:46.745113

"""

# revision identifiers, used by Alembic.
revision = 'adf671eddeb4'
down_revision = 'a86472389a70'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'environment_hierarchy_level'

    with op.batch_alter_table(table_name) as batch:
        batch.drop_constraint(
            table_prefix + 'environment_hierarchy_level_environment_id_fkey',
            type_='foreignkey'
        )
        batch.create_foreign_key(
            table_prefix + 'environment_hierarchy_level_environment_id_fkey',
            table_prefix + 'environment',
            ['environment_id'], ['id'], ondelete='CASCADE'
        )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'environment_hierarchy_level'
    with op.batch_alter_table(table_name) as batch:
        batch.drop_constraint(
            table_prefix + 'environment_hierarchy_level_environment_id_fkey',
            type_='foreignkey'
        )
        batch.create_foreign_key(
            table_prefix + 'environment_hierarchy_level_environment_id_fkey',
            table_prefix + 'environment',
            ['environment_id'], ['id']
        )
