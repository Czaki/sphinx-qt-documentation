#!/usr/bin/env bash

set -eux
pip install .
if [ ${1} == "no_install" ] ; then
  # This build supposed to fail with an exception, if it doesn't,
  # grep will return nonzero and thereby fail the CI step
  sphinx-build -W tests/document01 /tmp/build |& grep -q "RuntimeError"
else
  sphinx-build -W tests/document01 /tmp/build
fi
