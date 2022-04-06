"""
This module contains sphinx extension supporting for build PartSeg documentation.

this extension provides one configuration option:

`qt_documentation` with possible values:

 * PyQt5 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt5/api/ (incomplete)
 * Qt5 - linking to Qt5 documentation on "https://doc.qt.io/qt-5/" (default)
 * PySide2 - linking to PySide6 documentation on  "https://doc.qt.io/qtforpython-5/"
 * PyQt6 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt6/api/ (incomplete)
 * Qt6 - linking to Qt5 documentation on "https://doc.qt.io/qt-6/"
 * PySide6 - linking to PySide6 documentation on  "https://doc.qt.io/qtforpython/PySide6/"
"""
from typing import Any, Dict

from sphinx.application import Sphinx
from sphinx.config import ENUM

from sphinx_qt_documentation.utils import (
    autodoc_process_signature,
    missing_reference,
    patch_intersphinx_mapping,
)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension("sphinx.ext.autodoc")
    app.setup_extension("sphinx.ext.intersphinx")
    app.add_config_value(
        "qt_documentation",
        "Qt5",
        True,
        ENUM("Qt5", "PySide2", "PyQt5", "Qt6", "PySide6", "PyQt6"),
    )

    app.connect("missing-reference", missing_reference)
    app.connect("autodoc-process-signature", autodoc_process_signature)
    app.connect("config-inited", patch_intersphinx_mapping, priority=800)
    # app.connect('doctree-read', doctree_read)
    return {"version": "0.1", "env_version": 1, "parallel_read_safe": True}


# https://doc.qt.io/qtforpython/PySide6/QtWidgets/QListWidget.html#PySide6.QtWidgets.QListWidget.itemDoubleClicked
# https://doc.qt.io/qtforpython/PySide6/QtWidgets/QListWidget.html#
# PySide6.QtWidgets.PySide6.QtWidgets.QListWidget.itemDoubleClicked
