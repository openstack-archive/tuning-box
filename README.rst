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

API
---

For all operations authentication is required. Auth token should be passed in
the X-Auth-Token HTTP header. Tuning Box installed as a Fuel Nailgun extension
thus base API URL is placed at ``http://MASTER_NODE_IP:8000/api/v1/config``
All operations URLs should be concatenated with the base API URL.

Environments operations
=======================

URL: ``/environments``
Operations:

- (GET) list environments
- (POST) create environment

For environment creation POST:

.. code-block:: python

    {
        'hierarchy_levels': [
            # list of hierarchy levels
        ],
        'components': [
            # list of components ids
        ]
    }


Environment operations
======================

URL: ``/environments/<int:component_id>``
Operations:

- (GET) get environment
- (PUT/PATCH) update environment
- (DELETE) delete environment

Components operations
=====================

URL: ``/components``
Operations:

- (GET) list components
- (POST) create component

For component creation POST:

.. code-block:: python

    {
        'name': str,
        'resource_definitions': [
            {
                'name': str, 'content': str
            }
        ]
    }


Component operations
====================

URL: ``/components/<int:component_id>``
Operations:

- (GET) get component
- (PUT/PATCH) update component
- (DELETE) delete component

Hierarchy levels operations
===========================

URL: ``/environments/<int:environment_id>/hierarchy_levels``
Operations:

- (GET) list environment hierarchy levels

Hierarchy levels modifications performed via environment
modifications.

Hierarchy level operations
==========================

URL: ``/environments/<int:component_id>/<string:level>``
Operations:

- (GET) get hierarchy level

.. _`keys operations`:

Keys operations
===============

For performing keys operation send PATCH request to the appropriate URL. As data use
list of keys written in the order of access. For instance you have the following data:

.. code-block:: python

    {
        'k0': {
            'k1': 'val01',
            'k2': 'val02,
            'k3': [{'k4': 'val030'}]
        }
    }

For access to the val02 key path will be: ['k0', 'k2']
If you want to modify value add required value to the keys path. For instance, if you
want change 'val02' to 'val02_new' key paths will be: ['k0', 'k2', 'val02_new']

If you want to delete 'k4' key use key path ['k0', 'k3', 0, 'k4']

Key operations work only in batch mode, so you should pass list of keys paths to the
appropriate API handler::

    [['k0', 'k1', 'val01_new'], ['k0', 'k2', 'val02_new']]

For adding new key 'new_k' to the data you should send the following keys paths::

    [['new_k', 'new_val']]

Resource definitions operations
===============================

URL: ``/resource_definitions``
Operations:

- (GET) list resource definitions
- (POST) create resource definition

For resource definition creation POST:

.. code-block:: python

    {
        'name': str,
        'component_id': int,
        'content': str
    }


Resource definition operations
==============================

URL: ``/resource_definitions/<int:resource_definition_id>``
Operations:

- (GET) get resource definition
- (PUT/PATCH) update resource definition
- (DELETE) delete resource definition

Resource definition keys operations
===================================

Operations with keys modifies resource definition content only.
These operations supports nested keys. For details see: `keys operations`_.

URL: ``/resource_definitions/<int:resource_definition_id>/keys/<keys_operation:operation>``
Handled keys operations:

- get resource value key
- update resource definition key
- delete resource definition key

Resource values operations
==========================

URL: ``/environments/<int:environment_id>/<levels:levels>resources/<id_or_name:resource_id_or_name>/values``
Operations:

- (GET) get resource value
- (PUT) create/update resource value

For resource value creation set PUT HTTP request with data as workload.
This data will be stored to the resource values bound to the appropriate
level value.

For merging data from all levels specify 'effective' parameter for GET
HTTP request.

For tracing the level from which data is got specify 'show_lookup'
parameter for the GET HTTP request. Lookup has sense only if you are
fetching the effective values.

Resource values keys operations
===============================

Operations with keys modifies resource values only.
These operations supports nested keys. For details see: `keys operations`_.

URL: ``/environments/<int:environment_id>/<levels:levels>resources/<id_or_name:resource_id_or_name>/values/keys/<keys_operation:operation>``
Handled keys operations:

- get resource values key
- update resource values key
- delete resource values key

Resource overrides operations
=============================

URL: ``/environments/<int:environment_id>/<levels:levels>resources/<id_or_name:resource_id_or_name>/overrides``
Operations:

- (GET) get resource overrides
- (PUT) create/update resource overrides

For resource value creation set PUT HTTP request with data as workload.
This data will be stored to the resource override bound to the appropriate
level value.

Resource values keys operations
===============================

Operations with keys modifies resource overrides only.
These operations supports nested keys. For details see: `keys operations`_.

URL: ``/environments/<int:environment_id>/<levels:levels>resources/<id_or_name:resource_id_or_name>/overrides/keys/<keys_operation:operation>``
Handled keys operations:

- get resource value key
- update resource value key
- delete resource value key
