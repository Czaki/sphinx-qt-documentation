#!/usr/bin/env bash

set -eux
pip install .
if [ ${1} == "Qt_dot_py__PyQt5" ] ; then
  # PyQt5 import in Qt.py fails wo avail libGL
  apt update ; apt install -yq libglu1-mesa
fi
if [ ${1} == "no_install" ] ; then
  # This build supposed to fail with an exception, if it doesn't,
  # grep will return nonzero and thereby fail the CI step
  ~/.local/bin/sphinx-build -W tests/document01 /tmp/build |& grep -q "RuntimeError"
else
  ~/.local/bin/sphinx-build -W tests/document01 /tmp/build
fi
