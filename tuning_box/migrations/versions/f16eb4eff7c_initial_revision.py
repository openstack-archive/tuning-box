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

"""Initial revision

Revision ID: f16eb4eff7c
Revises:
Create Date: 2016-03-02 17:10:04.750584

"""

# revision identifiers, used by Alembic.
revision = 'f16eb4eff7c'
down_revision = None
branch_labels = None
depends_on = None

from alembic import context
from alembic import op
import sqlalchemy as sa

import tuning_box.db


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    op.create_table(
        table_prefix + 'component',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
    )
    op.create_table(
        table_prefix + 'environment',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    )
    op.create_table(
        table_prefix + 'namespace',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
    )
    table_name = table_prefix + 'environment_components'
    op.create_table(
        table_name,
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['component_id'], [table_prefix + 'component.id'],
            name=table_name + '_component_id_fkey',
        ),
        sa.ForeignKeyConstraint(
            ['environment_id'], [table_prefix + 'environment.id'],
            name=table_name + '_environment_id_fkey',
        ),
    )
    table_name = table_prefix + 'environment_hierarchy_level'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['environment_id'], [table_prefix + 'environment.id'],
            name=table_name + '_environment_id_fkey',
        ),
        sa.ForeignKeyConstraint(
            ['parent_id'], [table_prefix + 'environment_hierarchy_level.id'],
            name=table_name + '_parent_id_fkey',
        ),
        sa.UniqueConstraint(
            'environment_id', 'name',
            name=table_name + '_environment_id_name_key',
        ),
        sa.UniqueConstraint(
            'environment_id', 'parent_id',
            name=table_name[:-4] + '_environment_id_parent_id_key',
        ),
    )
    table_name = table_prefix + 'schema'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.Column('namespace_id', sa.Integer(), nullable=True),
        sa.Column('content', tuning_box.db.Json(), nullable=True),
        sa.ForeignKeyConstraint(
            ['component_id'], [table_prefix + 'component.id'],
            name=table_name + '_component_id_fkey'),
        sa.ForeignKeyConstraint(
            ['namespace_id'], [table_prefix + 'namespace.id'],
            name=table_name + '_namespace_id_fkey'),
    )
    table_name = table_prefix + 'template'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.Column('content', tuning_box.db.Json(), nullable=True),
        sa.ForeignKeyConstraint(
            ['component_id'], [table_prefix + 'component.id'],
            name=table_name + '_component_id_fkey',
        ),
    )
    table_name = table_prefix + 'environment_hierarchy_level_value'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('level_id', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ['level_id'], [table_prefix + 'environment_hierarchy_level.id'],
            name=table_name + '_level_id_fkey',
        ),
        sa.ForeignKeyConstraint(
            ['parent_id'], [table_name + '.id'],
            name=table_name + '_parent_id_fkey',
        ),
    )
    table_name = table_prefix + 'environment_schema_values'
    op.create_table(
        table_name,
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('schema_id', sa.Integer(), nullable=True),
        sa.Column('level_value_id', sa.Integer(), nullable=True),
        sa.Column('values', tuning_box.db.Json(), nullable=True),
        sa.ForeignKeyConstraint(
            ['environment_id'], [table_prefix + 'environment.id'],
            name=table_name + '_environment_id_fkey',
        ),
        sa.ForeignKeyConstraint(
            ['level_value_id'],
            [table_prefix + 'environment_hierarchy_level_value.id'],
            name=table_name + '_level_value_id_fkey',
        ),
        sa.ForeignKeyConstraint(
            ['schema_id'], [table_prefix + 'schema.id'],
            name=table_name + '_schema_id_fkey',
        ),
        sa.UniqueConstraint(
            'environment_id', 'schema_id', 'level_value_id',
            name=table_name[:-6] + 'environment_id_schema_id_leve_key',
        ),
    )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    op.drop_table(table_prefix + 'environment_schema_values')
    op.drop_table(table_prefix + 'environment_hierarchy_level_value')
    op.drop_table(table_prefix + 'template')
    op.drop_table(table_prefix + 'schema')
    op.drop_table(table_prefix + 'environment_hierarchy_level')
    op.drop_table(table_prefix + 'environment_components')
    op.drop_table(table_prefix + 'namespace')
    op.drop_table(table_prefix + 'environment')
    op.drop_table(table_prefix + 'component')
