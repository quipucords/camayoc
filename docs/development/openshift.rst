OpenShift Tests
===============

.. caution::
   Work in Progress! This documentation is a place for describing how to test Quipucords inspection of OpenShift clusters (OCP) with Camayoc.

For running the Ansible Playbook to deploy a simple project to OpenShift, please make sure to have the OpenShift command-line interface (CLI) installed. Refer to the `oc <https://docs.openshift.com/container-platform/4.11/cli_reference/openshift_cli/getting-started-cli.html>`_ command for more information.

Verify if you have the CLI installed:

.. sourcecode:: shell

   oc version
   Client Version: 4.11.0-0.nightly-2022-05-18-171831
   Kustomize Version: v4.5.4
   Server Version: 4.10.43
   Kubernetes Version: v1.23.12+8a6bfe4
