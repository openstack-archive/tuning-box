==========
Tuning Box
==========

Tuning Box is a configuration storage for your clouds.

Tuning Box can be used as a centralized storage for all configurations. It
supports Keystone authentication. By default, Tuning Box installs as a Fuel
extension but also it can be run as a service.

* Free software: `Apache license`_
* Source_
* Bugs_

.. _Source: https://github.com/openstack/tuning-box
.. _Bugs: https://bugs.launchpad.net/fuel/+bugs?field.searchtext=&orderby=-importance&search=Search&field.tag=area-configdb+
.. _Apache license: https://www.apache.org/licenses/LICENSE-2.0

Features
--------

ConfigDB entities:

- Environment
- Component
- Hierarchy level
- Resource definition
- Resource value
- Resource value override

Installation
------------

#. Download Tuning Box RPM package or code to the Fuel Master node. The
   package can be built from the source code using::

    $ python setup.py bdist_rpm

#. Tuning Box installs as a Fuel Nailgun extension. Therefore, perform the
   DB migration and restart the Nailgun service::

    $ nailgun_syncdb
    $ systemctl restart nailgun.service

#. Configure the Tuning Box keystone service::

    $ export OS_USERNAME=admin OS_PASSWORD=admin OS_PROJECT_NAME=admin OS_AUTH_URL=http://10.20.0.2:5000
    $ openstack service create --name tuning-box config
    $ openstack endpoint create --publicurl http://10.20.0.2:8000/api/config --region RegionOne tuning-box

Now, you have enabled a set of ``config`` commands in the ``fuel2`` CLI.

Commands groups for fuel2 CLI
-----------------------------

The ``fuel2`` CLI commands groups are the following:

- ``config comp`` - CRUD operations for components
- ``config def`` - CRUD operations for resource definitions
- ``config env`` - CRUD operations for environments
- ``config get``, ``config set``, ``config del`` - CRUD operations for
  resource values
- ``config override``, ``config rm override`` - operations for resource values
  overrides
