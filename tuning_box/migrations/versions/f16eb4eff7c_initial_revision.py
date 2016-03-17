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
    op.create_table(
        table_prefix + 'environment_components',
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['component_id'], [table_prefix + 'component.id']),
        sa.ForeignKeyConstraint(
            ['environment_id'], [table_prefix + 'environment.id']),
    )
    op.create_table(
        table_prefix + 'environment_hierarchy_level',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['environment_id'], [table_prefix + 'environment.id']),
        sa.ForeignKeyConstraint(
            ['parent_id'], [table_prefix + 'environment_hierarchy_level.id']),
        sa.UniqueConstraint('environment_id', 'name'),
        sa.UniqueConstraint('environment_id', 'parent_id'),
    )
    op.create_table(
        table_prefix + 'schema',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.Column('namespace_id', sa.Integer(), nullable=True),
        sa.Column('content', tuning_box.db.Json(), nullable=True),
        sa.ForeignKeyConstraint(
            ['component_id'], [table_prefix + 'component.id']),
        sa.ForeignKeyConstraint(
            ['namespace_id'], [table_prefix + 'namespace.id']),
    )
    op.create_table(
        table_prefix + 'template',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.Column('content', tuning_box.db.Json(), nullable=True),
        sa.ForeignKeyConstraint(
            ['component_id'], [table_prefix + 'component.id']),
    )
    op.create_table(
        table_prefix + 'environment_hierarchy_level_value',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('level_id', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ['level_id'], [table_prefix + 'environment_hierarchy_level.id']),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            [table_prefix + 'environment_hierarchy_level_value.id']),
    )
    op.create_table(
        table_prefix + 'environment_schema_values',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('schema_id', sa.Integer(), nullable=True),
        sa.Column('level_value_id', sa.Integer(), nullable=True),
        sa.Column('values', tuning_box.db.Json(), nullable=True),
        sa.ForeignKeyConstraint(
            ['environment_id'], [table_prefix + 'environment.id']),
        sa.ForeignKeyConstraint(
            ['level_value_id'],
            [table_prefix + 'environment_hierarchy_level_value.id']),
        sa.ForeignKeyConstraint(['schema_id'], [table_prefix + 'schema.id']),
        sa.UniqueConstraint('environment_id', 'schema_id', 'level_value_id'),
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
