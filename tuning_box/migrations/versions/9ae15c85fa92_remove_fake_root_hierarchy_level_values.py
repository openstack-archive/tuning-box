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

"""Remove fake root hierarchy level values

Revision ID: 9ae15c85fa92
Revises: d054eefc4c5b
Create Date: 2016-04-12 20:22:06.323291

"""

# revision identifiers, used by Alembic.
revision = '9ae15c85fa92'
down_revision = 'd054eefc4c5b'
branch_labels = None
depends_on = None

from alembic import context
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext import automap


def _get_autobase(table_prefix, bind):
    metadata = sa.MetaData(bind=bind)
    table_name = table_prefix + 'environment_hierarchy_level_value'
    metadata.reflect(only=[table_name])
    AutoBase = automap.automap_base(metadata=metadata)

    def classname_for_table(base, refl_table_name, table):
        assert refl_table_name.startswith(table_prefix)
        noprefix_name = refl_table_name[len(table_prefix):]
        uname = u"".join(s.capitalize() for s in noprefix_name.split('_'))
        if not isinstance(uname, str):
            return uname.encode('utf-8')
        else:
            return uname

    AutoBase.prepare(classname_for_table=classname_for_table)
    return AutoBase


def _get_ehlv_class():
    table_prefix = context.config.get_main_option('table_prefix')
    bind = op.get_bind()
    AutoBase = _get_autobase(table_prefix, bind)
    return AutoBase.classes.EnvironmentHierarchyLevelValue


def _get_session():
    return sa.orm.Session(bind=op.get_bind(), autocommit=True)


def upgrade():
    EHLV = _get_ehlv_class()
    session = _get_session()
    with session.begin():
        fake_roots = session.query(EHLV) \
            .filter_by(level_id=None, parent_id=None, value=None) \
            .all()
        if fake_roots:
            fake_root_ids = [r.id for r in fake_roots]
            session.query(EHLV) \
                .filter(EHLV.parent_id.in_(fake_root_ids)) \
                .update({EHLV.parent_id: None}, synchronize_session=False)
            for r in fake_roots:
                session.delete(r)


def downgrade():
    EHLV = _get_ehlv_class()
    session = _get_session()
    with session.begin():
        fake_root = EHLV(level_id=None, parent_id=None, value=None)
        session.add(fake_root)
        session.flush()
        session.query(EHLV) \
            .filter(EHLV.parent_id == None,  # noqa
                    EHLV.id != fake_root.id) \
            .update({EHLV.parent_id: fake_root.id},
                    synchronize_session=False)
