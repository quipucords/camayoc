#!/usr/bin/env bash
set -euo pipefail

DUPLICATED_IDS=$(
    grep -r -i --include "*.py" :id: camayoc/tests | sort -k 2 | uniq -d -f 2)

if [ "${DUPLICATED_IDS}" ]; then
    echo "Found duplicated test case IDs:"
    echo
    echo -n "${DUPLICATED_IDS}"
    echo
    exit 1
fi
