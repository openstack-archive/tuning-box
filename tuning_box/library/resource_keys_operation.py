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

import copy

import flask

from tuning_box import db
from tuning_box import errors
from tuning_box import library


class KeysOperationMixin(object):

    OPERATION_SET = 'set'
    OPERATION_DELETE = 'delete'

    OPERATIONS = (OPERATION_SET, OPERATION_DELETE)

    def _check_out_of_index(self, cur_point, key, keys_path):
        if isinstance(cur_point, (list, tuple)) and key >= len(cur_point):
            raise errors.KeysPathNotExisted(
                "Keys path doesn't exist {0}. "
                "Failed on the key {1}".format(keys_path, key)
            )

    def _check_key_existed(self, cur_point, key, keys_path):
        if isinstance(cur_point, dict) and key not in cur_point:
            raise errors.KeysPathNotExisted(
                "Keys path doesn't exist {0}. "
                "Failed on the key {1}".format(keys_path, key)
            )

    def _check_path_is_reachable(self, cur_point, key, keys_path):
        if not isinstance(cur_point, (list, tuple, dict)):
            raise errors.KeysPathUnreachable(
                "Leaf value {0} found on key {1} "
                "in keys path {2}".format(cur_point, key, keys_path)
            )

    def do_set(self, storage, keys_paths):
        """Sets values from keys paths to storage.

        Keys path is list of keys paths. If we have keys_paths
        [['a', 'b', 'val']], then storage['a']['b'] will be set to 'val'.
        Last value in the keys path is value to be set.

        :param storage: original data
        :param keys_paths: lists of keys paths to be set
        :returns: result of merging keys_paths and storage
        """

        storage_copy = copy.deepcopy(storage)
        for keys_path in keys_paths:
            cur_point = storage_copy
            if len(keys_path) < 2:
                raise errors.KeysPathInvalid(
                    "Keys path {0} invalid. Keys path should contain "
                    "at least one key and value".format(keys_path)
                )

            for key in keys_path[:-2]:
                self._check_path_is_reachable(cur_point, key, keys_path)
                self._check_out_of_index(cur_point, key, keys_path)
                self._check_key_existed(cur_point, key, keys_path)
                cur_point = cur_point[key]

            assign_to = keys_path[-2]
            self._check_out_of_index(cur_point, assign_to, keys_path)
            cur_point[assign_to] = keys_path[-1]

        return storage_copy

    def do_delete(self, storage, keys_paths):
        """Deletes keys paths from storage.

        Keys path is list of keys paths. If we have keys_paths
        [['a', 'b']], then storage['a']['b'] will be removed.

        :param storage: data
        :param keys_paths: lists of keys paths to be deleted
        :returns: result of keys_paths deletion from storage
        """

        storage_copy = copy.deepcopy(storage)
        for keys_path in keys_paths:
            cur_point = storage_copy
            if not keys_path:
                continue

            try:
                for key in keys_path[:-1]:
                    cur_point = cur_point[key]
                key = keys_path[-1]
                self._check_path_is_reachable(cur_point, key, keys_path)
                del cur_point[key]
            except (KeyError, IndexError):
                raise errors.KeysPathNotExisted(
                    "Keys path doesn't exist {0}. "
                    "Failed on the key {1}".format(keys_path, key)
                )
        return storage_copy

    def perform_operation(self, operation, storage, keys_paths):
        if operation == self.OPERATION_SET:
            return self.do_set(storage, keys_paths)
        elif operation == self.OPERATION_DELETE:
            return self.do_delete(storage, keys_paths)
        else:
            raise errors.UnknownKeysOperation(
                "Unknown operation: {0}. "
                "Allowed operations: {1}".format(operation, self.OPERATIONS)
            )


class ResourceKeysMixin(KeysOperationMixin):

    @db.with_transaction
    def _do_update(self, environment_id, levels,
                   resource_id_or_name, operation, storage_name):

        environment = db.Environment.query.get_or_404(environment_id)
        res_def = library.get_resource_definition(
            resource_id_or_name, environment_id)

        if res_def.id != resource_id_or_name:
            from tuning_box.app import api
            return flask.redirect(api.url_for(
                self.__class__,
                environment_id=environment_id,
                levels=levels,
                resource_id_or_name=res_def.id,
            ), code=308)

        res_values = library.get_resource_values(environment, levels, res_def)
        result = self.perform_operation(
            operation, getattr(res_values, storage_name), flask.request.json)
        setattr(res_values, storage_name, result)
