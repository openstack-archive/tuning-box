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

from sqlalchemy.orm import exc as sa_exc

from tuning_box import db
from tuning_box import errors


def load_objects(model, ids):
    if ids is None:
        return None
    result = []
    for obj_id in ids:
        obj = model.query.filter_by(id=obj_id).one_or_none()
        if obj is None:
            raise errors.TuningboxNotFound(
                "{0} not found by identifier: "
                "{1}".format(model.__tablename__, obj_id)
            )
        result.append(obj)
    return result


def load_objects_by_id_or_name(model, identifiers):
    if identifiers is None:
        return None
    result = []
    for identifier in identifiers:
        obj = model.query.get_by_id_or_name(
            identifier, fail_on_none=False)
        if obj is None:
            raise errors.TuningboxNotFound(
                "{0} not found by identifier: "
                "{1}".format(model.__tablename__, identifier)
            )
        result.append(obj)
    return result


def get_resource_definition(id_or_name, environment_id):
    query = db.ResourceDefinition.query.join(db.Component). \
        join(db.Environment.environment_components_table). \
        filter_by(environment_id=environment_id)

    if isinstance(id_or_name, int):
        query = query.filter(db.ResourceDefinition.id == id_or_name)
    else:
        query = query.filter(db.ResourceDefinition.name == id_or_name)

    result = query.all()

    if not result:
        raise errors.TuningboxNotFound(
            "{0} not found by {1} in environment {2}".format(
                db.ResourceDefinition.__tablename__,
                id_or_name,
                environment_id
            )
        )
    elif len(result) > 1:
        raise sa_exc.MultipleResultsFound

    return result[0]
