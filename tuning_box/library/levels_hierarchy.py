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

import werkzeug

from tuning_box import db


def iter_environment_level_values(environment, levels):
    env_levels = db.EnvironmentHierarchyLevel.get_for_environment(environment)
    level_pairs = zip(env_levels, levels)
    parent_level_value = None
    for env_level, (level_name, level_value) in level_pairs:
        if env_level.name != level_name:
            raise werkzeug.exceptions.BadRequest(
                "Unexpected level name '{0}'. Expected '{1}'.".format(
                    level_name, env_level.name))
        level_value_db = db.get_or_create(
            db.EnvironmentHierarchyLevelValue,
            level=env_level,
            parent=parent_level_value,
            value=level_value,
        )
        yield level_value_db
        parent_level_value = level_value_db


def get_environment_level_value(environment, levels):
    level_value = None
    for level_value in iter_environment_level_values(environment, levels):
        pass
    return level_value
