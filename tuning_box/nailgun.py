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

from __future__ import absolute_import

import itertools
import threading

from flask import current_app as cur_app
from nailgun.db import sqlalchemy as nailgun_sa
from nailgun import extensions
import web

import tuning_box
from tuning_box import app as tb_app
from tuning_box import db as tb_db
from tuning_box import hiera_config


class App2WebPy(web.application):
    def __init__(self):
        web.application.__init__(self)
        self.__name__ = self
        self.app = None
        self.lock = threading.Lock()

    def create_app(self):
        raise NotImplementedError

    def get_app(self):
        with self.lock:
            if not self.app:
                self.app = self.create_app()
            return self.app

    def handle(self):
        written_data = []

        def write(data):
            assert start_response.called
            written_data.append(data)

        def start_response(status, headers, exc_info=None):
            assert not start_response.called
            assert not exc_info
            start_response.called = True
            web.ctx.status = status
            web.ctx.headers.extend(headers)
            return write

        start_response.called = False

        app = self.get_app()
        environ = dict(web.ctx.environ)
        environ["SCRIPT_NAME"] = environ["PATH_INFO"][:-len(web.ctx.path)]
        environ["PATH_INFO"] = environ["REQUEST_URI"] = web.ctx.path
        result = app(environ, start_response)
        return itertools.chain(written_data, result)


class TB2WebPy(App2WebPy):
    def create_app(self):
        # Nailgun API already contains keystone middleware
        app = tb_app.build_app(with_keystone=False)
        tb_db.prefix_tables(tb_db, Extension.table_prefix())
        app.config["PROPAGATE_EXCEPTIONS"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = nailgun_sa.db_str
        return app


class ConfigPipeline(extensions.BasePipeline):

    def get_hierarchy(self):
        config = hiera_config.load_config()
        return config['hierarchy']

    @classmethod
    def process_deployment_for_cluster(cls, cluster, cluster_data):
        """Extend or modify deployment data for cluster.

        :param cluster_data: serialized data for cluster
        :param cluster: the instance of Cluster
        """
        result = {}
        for level in cls.get_hierarchy():
            cur_app.logger.debug("Fetching info for hierarchy level: %s",
                                 level)
        return cluster_data.update(result)


class Extension(extensions.BaseExtension):
    name = 'tuning_box'
    version = tuning_box.__version__
    description = 'Plug tuning_box endpoints into Nailgun itself'
    app = TB2WebPy()

    urls = [{'uri': '/config', 'handler': app}]

    @classmethod
    def alembic_migrations_path(cls):
        app_instance = cls.app.get_app()
        with app_instance.app_context():
            app_instance.logger.error("##############################")
            from tuning_box.library.resource_values import execute_sql
            execute_sql()
        return tuning_box.get_migrations_dir()
