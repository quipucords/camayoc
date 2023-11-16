.. _quipucords: https://github.com/quipucords/quipucords
.. _qpc: https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/

=======
Camayoc
=======

A GPL-licensed Python library that facilitates functional testing of quipucords_.

.. image:: https://github.com/quipucords/camayoc/actions/workflows/tests.yml/badge.svg?branch=master
   :target: https://github.com/quipucords/camayoc/actions/workflows/tests.yml?query=branch%3Amaster
.. image:: https://codecov.io/gh/quipucords/camayoc/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/quipucords/camayoc


Installation
^^^^^^^^^^^^

Camayoc supports Python 3.11. It uses `Poetry <https://python-poetry.org/>`_
for dependency and virtual environment management. See Poetry documentation for
installation instructions - one of the easier paths is to install it through
`pipx <https://pypa.github.io/pipx/>`_ , which you can get from your distribution.

This is a suggested install method:

1. Install pipx and Poetry:

    sudo dnf install -y pipx
    pipx install poetry

2. Clone the repo and navigate to the base directory::

    git clone https://github.com/quipucords/camayoc.git
    cd camayoc

3. Install using make targets::

    # To install for development, install all dependencies
    make install-dev
    # If you only want to run the test suite, you can skip
    # a few dependencies with the plain "install" target
    make install

Configuration
^^^^^^^^^^^^^

Camayoc requires a configuration file to be installed to
``$XDG_CONFIG_HOME/camayoc/config.yaml``. On most systems this will be
``~/.config/camayoc/config.yaml``.

The config file tells Camayoc about the hosts you would like to run tests
against and the credentials to use with these hosts. It also tells Camayoc
where the quipucords_ server you want to test is running so the tests can
execute against the server.

Camayoc contains test suites for quipucords/qpc and quipucords/quipucords
projects. All portions of the test suite expect the same
config file format.  Any changes to the test suite that require changes to the
config file format should be made with this in mind.

There is an example annotated config file in ``example_config.yaml`` in
the root directory of the Camayoc repository.

Configuration Template
""""""""""""""""""""""

The Jenkins automation jobs often use a template configuration file when
running camaoyc. This template config has default values (such as
``${jenkins_ssh_file}``) that are swapped out for values which Jenkins
provides.  Additionally, ssh key files need to be set with the proper
permissions.

When working locally or in a dev environment, these steps can be automatically
configured with a template config using the ``configure-camayoc.yaml`` playbook
found in the ``camayoc/scripts/`` directory. To use the playbook, first open it
and set the variables at the top accordingly (or overwrite them when calling
the playbook using ``-e`` flags). Then, assuming the template configuration has
been downloaded and defined correctly in the playbook, run the playbook::

    cd scripts
    sudo ansible-playbook configure-camayoc.yaml



Configuring py.test
^^^^^^^^^^^^^^^^^^^

If you are testing machines that use ``https`` but do not have good
certificates, it can get difficult to read the test results due to warnings
about insecure connections. If this is a problem for you, an example
``pytest.ini`` file is provided in the root of the ``Camayoc`` repository that
disables these warnings. Additional configuration is possible through the
``pytest.ini`` file, these options are documented at
https://docs.pytest.org/en/latest/reference.html#ini-options-ref

For example, if you always want to run ``py.tests`` in verbose mode, this can
be done in the ``pytest.ini`` file.

Running The Test Suite
^^^^^^^^^^^^^^^^^^^^^^

Camayoc uses ``py.test`` as its test runner. The pytest project has excellent
documentation available at https://docs.pytest.org/en/latest/contents.html

Running Tests For quipucords_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run all the quipucords_ tests, first start the quipucords_ server
and set up your config file to point to the server. You should also
install the qpc_ executable in such a way that it is available in your
``$PATH``. Then run all API, CLI, and UI tests with::

    make test-qpc

.. warning::
    There are extra considerations you must take if you are running the
    quipucords server in a container.  First, your config file must use
    paths for sshkeys that exist on the server.
    Additionally you must map your ``/tmp`` directory to the server's ``/tmp``
    directory  because some tests create temporary files in ``/tmp`` that
    must be accessed by the server.


To only test the API, CLI, or UI, you can take advantage of the
following make targets::

    # for API tests only
    make test-qpc-api
    # for CLI tests only
    make test-qpc-cli
    # for UI tests only
    make test-qpc-ui

Additionally you can select tests based on string matching. For
example, to run quipucords tests with ``create`` in the name and skip
any others, run::

    make test-qpc PYTEST_OPTIONS="--verbose -k create"

Any other valid pytest options may be included as well in this
variable.

Testing Camayoc
^^^^^^^^^^^^^^^
Testing Camayoc requires that you have installed the development dependencies. Do that by running ``make install-dev``.

To run all checks of the Camayoc test framework, execute::

    make all
