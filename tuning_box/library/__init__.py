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


def load_objects_by_names_or_ids(model, ids):
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
