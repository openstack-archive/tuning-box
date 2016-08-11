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

"""Cascade deletion

Revision ID: 0c586adad733
Revises: 9ae15c85fa92
Create Date: 2016-08-11 10:05:51.127370

"""

# revision identifiers, used by Alembic.
revision = '0c586adad733'
down_revision = '9ae15c85fa92'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op


def upgrade():
    table_prefix = context.config.get_main_option('table_prefix')

    # Environment components
    op.drop_constraint(
        table_prefix + 'environment_components_component_id_fkey',
        table_prefix + 'environment_components',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'environment_components_component_id_fkey',
        table_prefix + 'environment_components',
        table_prefix + 'component',
        ['component_id'], ['id'], ondelete='CASCADE'
    )

    # Resource values
    op.drop_constraint(
        table_prefix + 'environment_schema_values_environment_id_fkey',
        table_prefix + 'resource_values', type_='foreignkey')
    op.create_foreign_key(
        table_prefix + 'resource_values_environment_id_fkey',
        table_prefix + 'resource_values',
        table_prefix + 'environment',
        ['environment_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint(
        table_prefix + 'resource_values_resource_definition_id_fkey',
        table_prefix + 'resource_values',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'resource_values_resource_definition_id_fkey',
        table_prefix + 'resource_values',
        table_prefix + 'resource_definition',
        ['resource_definition_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_constraint(
        table_prefix + 'environment_schema_values_level_value_id_fkey',
        table_prefix + 'resource_values',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'environment_resource_values_level_value_id_fkey',
        table_prefix + 'resource_values',
        table_prefix + 'environment_hierarchy_level_value',
        ['level_value_id'], ['id'], ondelete='CASCADE'
    )

    # Resource definition
    op.drop_constraint(
        table_prefix + 'schema_component_id_fkey',
        table_prefix + 'resource_definition',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'resource_definition_component_id_fkey',
        table_prefix + 'resource_definition',
        table_prefix + 'component',
        ['component_id'], ['id'], ondelete='CASCADE'
    )


def downgrade():
    table_prefix = context.config.get_main_option('table_prefix')

    # Resource definition
    op.drop_constraint(
        table_prefix + 'resource_definition_component_id_fkey',
        table_prefix + 'resource_definition',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'schema_component_id_fkey',
        table_prefix + 'resource_definition',
        table_prefix + 'component',
        ['component_id'], ['id']
    )

    # Resource values
    op.drop_constraint(
        table_prefix + 'environment_resource_values_level_value_id_fkey',
        table_prefix + 'resource_values',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'environment_schema_values_level_value_id_fkey',
        table_prefix + 'resource_values',
        table_prefix + 'environment_hierarchy_level_value',
        ['level_value_id'], ['id']
    )

    op.drop_constraint(
        table_prefix + 'resource_values_resource_definition_id_fkey',
        table_prefix + 'resource_values', type_='foreignkey')
    op.create_foreign_key(
        table_prefix + 'resource_values_resource_definition_id_fkey',
        table_prefix + 'resource_values',
        table_prefix + 'resource_definition',
        ['resource_definition_id'], ['id']
    )

    op.drop_constraint(
        table_prefix + 'resource_values_environment_id_fkey',
        table_prefix + 'resource_values', type_='foreignkey')
    op.create_foreign_key(
        table_prefix + 'environment_schema_values_environment_id_fkey',
        table_prefix + 'resource_values',
        table_prefix + 'environment',
        ['environment_id'], ['id']
    )

    # Environment components
    op.drop_constraint(
        table_prefix + 'environment_components_component_id_fkey',
        table_prefix + 'environment_components',
        type_='foreignkey'
    )
    op.create_foreign_key(
        table_prefix + 'environment_components_component_id_fkey',
        table_prefix + 'environment_components',
        table_prefix + 'component',
        ['component_id'], ['id']
    )
