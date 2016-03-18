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

"""Switch to new API

Revision ID: 3b2a0f134e45
Revises: f16eb4eff7c
Create Date: 2016-03-17 16:30:11.989340

"""

# revision identifiers, used by Alembic.
revision = '3b2a0f134e45'
down_revision = 'f16eb4eff7c'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op
import sqlalchemy as sa

import tuning_box.db


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    op.drop_table(table_prefix + 'template')
    table_name = table_prefix + 'environment_schema_values'
    with op.batch_alter_table(table_name) as batch:
        batch.drop_constraint(table_name + '_schema_id_fkey', 'foreignkey')
        batch.alter_column(
            'schema_id',
            new_column_name='resource_definition_id',
            existing_type=sa.Integer(),
        )
    op.rename_table(table_name, table_prefix + 'resource_values')
    op.rename_table(table_prefix + 'schema',
                    table_prefix + 'resource_definition')
    with op.batch_alter_table(table_prefix + 'resource_definition') as batch:
        batch.drop_column('namespace_id')
    op.drop_table(table_prefix + 'namespace')
    table_name = table_prefix + 'resource_values'
    with op.batch_alter_table(table_name) as batch:
        batch.create_foreign_key(
            table_name + '_resource_definition_id_fkey',
            table_prefix + 'resource_definition',
            ['resource_definition_id'],
            ['id'],
        )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')
    table_name = table_prefix + 'resource_values'
    with op.batch_alter_table(table_name) as batch:
        batch.drop_constraint(table_name + '_resource_definition_id_fkey',
                              'foreignkey')
    op.create_table(
        table_prefix + 'namespace',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=True),
    )
    table_name = table_prefix + 'schema'
    op.rename_table(table_prefix + 'resource_definition', table_name)
    with op.batch_alter_table(table_name) as batch:
        batch.add_column(
            sa.Column('namespace_id', sa.Integer(), nullable=True))
    table_name = table_prefix + 'environment_schema_values'
    op.rename_table(table_prefix + 'resource_values', table_name)
    with op.batch_alter_table(table_name) as batch:
        batch.alter_column(
            'resource_definition_id',
            new_column_name='schema_id',
            existing_type=sa.Integer(),
        )
        batch.create_foreign_key(
            table_name + '_schema_id_fkey',
            table_prefix + 'schema',
            ['schema_id'],
            ['id'],
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
