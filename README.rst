==========
Tuning Box
==========

Tuning Box - configuration storage for your clouds

Tuning Box can be used as centralized storage for all configurations. It
supports Keystone auth. By default installs as Fuel extension but also can
be run as a service.

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

Download Tuning Box RPM package or code to the master node. Package can be
built from the source code with::

    $ python setup.py bdist_rpm

Tuning Box installed as Fuel Nailgun extension so we need to perform
DB migration and restart the Nailgun service::

    $ nailgun_syncdb
    $ systemctl restart nailgun.service

Configure Tuning Box keystone service::

    $ export OS_USERNAME=admin OS_PASSWORD=admin OS_PROJECT_NAME=admin OS_AUTH_URL=http://10.20.0.2:5000
    $ openstack service create --name tuning-box config
    $ openstack endpoint create --publicurl http://10.20.0.2:8000/api/config --region RegionOne tuning-box

Now we have enabled set of 'config' commands in the fuel2 CLI.

fuel2 CLI commands groups:

- config comp - CRUD operations for components,
- config def - CRUD operations for resource definitions,
- config env - CRUD operations for environments,
- config get, set, del - CRUD operations for resource values,
- config override, rm override - operations for resource values overrides.
