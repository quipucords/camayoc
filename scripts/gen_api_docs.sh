#!/usr/bin/env bash
#
# For each file found by `find`, generate a entry on the toctree in
# `docs/api.rst`.
#
# NOTE: This script should be run from the repository docs directory. That is,
# this script should be run from this script's ../docs directory.

set -euo pipefail

# Recreate the api toctree document with its header
cat >"api.rst" <<EOF
API Documentation
=================

This is the Camayoc API documentation. It is mostly auto generated from the
source code. This section of the documentation should be treated as a handy
reference for developers, not a gospel.

.. toctree::

EOF

# List every rst file on the toctree
find api -type f -name '*.rst' | sed "s/.rst$//" | sort | while read file_name; do
    echo "    ${file_name}" >>"api.rst"
done
