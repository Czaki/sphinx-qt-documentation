# Sphinx Qt documentation

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Czaki/sphinx-qt-documentation/master.svg)](https://results.pre-commit.ci/latest/github/Czaki/sphinx-qt-documentation/master)
[![Tests](https://github.com/Czaki/sphinx-qt-documentation/actions/workflows/test.yaml/badge.svg)](https://github.com/Czaki/sphinx-qt-documentation/actions/workflows/test.yaml)
[![PyPI version](https://badge.fury.io/py/sphinx-qt-documentation.svg)](https://badge.fury.io/py/sphinx-qt-documentation)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


This is plugin to add cross-link to qt documentation for python code created with PyQt5 or PySide2.

Currently, it supports `qtpy`, `Qt.py` wrappers and `PyQt5`, `PySide2`, `PyQt6` and`PySide6`.

This extension provides one configuration option:

`qt_documentation` with possible values:

* PyQt5 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt5/api/ (incomplete)
* Qt5 - linking to Qt5 documentation on "https://doc.qt.io/qt-5/" (default)
* PySide2 - linking to PySide6 documentation on  "https://doc.qt.io/qtforpython-5/"
* PyQt6 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt6/api/ (incomplete)
* Qt6 - linking to Qt5 documentation on "https://doc.qt.io/qt-6/"
* PySide6 - linking to PySide6 documentation on  "https://doc.qt.io/qtforpython/PySide6/"

For default this extension use `inv` file from PyQt5 to resolve objects.
to overwrite this behaviour set another url for `intersphinx_mapping[PyQt5]` ex.:

```python
intersphinx_mapping = {...
                       "PyQt5": (custom_url, None),
                       ...}
```

This package currently does not support linking PyQt5 documentation using PySide2 `.inv` file
