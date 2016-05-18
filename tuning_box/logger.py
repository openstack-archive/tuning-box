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

import logging


def get_formatter():
    date_format = "%Y-%m-%d %H:%M:%S"
    log_format = "%(asctime)s.%(msecs)03d %(levelname)s " \
                 "(%(module)s) %(message)s"
    return logging.Formatter(fmt=log_format, datefmt=date_format)


def init_logger(log_level):
    handler = logging.StreamHandler()
    handler.setFormatter(get_formatter())
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(log_level)
