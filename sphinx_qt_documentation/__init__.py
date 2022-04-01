"""
This module contains sphinx extension supporting for build PartSeg documentation.

this extension provides one configuration option:

`qt_documentation` with possible values:

 * PyQt6 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt6/api/ (incomplete)
 * Qt6 - linking to Qt5 documentation on "https://doc.qt.io/qt-6/" (default)
 * PySide6 - linking to PySide2 documentation on  "https://doc.qt.io/qtforpython/PySide6/"
"""
from typing import Any, Dict

from sphinx.application import Sphinx
from sphinx.config import ENUM

from sphinx_qt_documentation._missing_reference import (
    _get_signal_and_version,
    autodoc_process_signature,
    missing_reference,
)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension("sphinx.ext.autodoc")
    app.setup_extension("sphinx.ext.intersphinx")
    app.add_config_value(
        "qt_documentation",
        "Qt6",
        True,
        ENUM("Qt5", "PySide2", "PyQt5", "Qt6", "PySide6", "PyQt6"),
    )

    url_mapping = {
        "PySide6": "https://doc.qt.io/qtforpython-6/",
        "PyQt6": "https://www.riverbankcomputing.com/static/Docs/PyQt6",
        "PySide2": "https://doc.qt.io/qtforpython-5/",
        "PyQt5": "https://www.riverbankcomputing.com/static/Docs/PyQt5",
    }

    name = getattr(app.config, "qt_documentation", "Qt6")

    if name == "Qt5":
        name = "PyQt5"
    elif name == "Qt6":
        name = "PyQt6"

    url = url_mapping[name]

    if hasattr(app.config, "intersphinx_mapping"):
        if name not in app.config.intersphinx_mapping:
            app.config.intersphinx_mapping[name] = (url, None)
    else:
        app.config.intersphinx_mapping = {name: (url, None)}
    app.connect("missing-reference", missing_reference)
    app.connect("autodoc-process-signature", autodoc_process_signature)
    # app.connect('doctree-read', doctree_read)
    return {"version": "0.1", "env_version": 1, "parallel_read_safe": True}


# https://doc.qt.io/qtforpython/PySide6/QtWidgets/QListWidget.html#PySide6.QtWidgets.QListWidget.itemDoubleClicked
# https://doc.qt.io/qtforpython/PySide6/QtWidgets/QListWidget.html#
# PySide6.QtWidgets.PySide6.QtWidgets.QListWidget.itemDoubleClicked
