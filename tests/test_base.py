# pylint: disable=C0114
# import subprocess
from pathlib import Path
from typing import List

import pytest
from sphinx.cmd.build import build_main


def create_conf(dir_path: Path, extensions: List[str], additional: str = ""):
    with open(dir_path / "conf.py", "w") as f_p:
        f_p.write(CONF_TEMPLATE.format(extensions, additional))


def create_index(dir_path: Path):
    with open(dir_path / "index.rst", "w") as f_p:
        f_p.write(INDEX_TEMPLATE)


def test_simple(tmp_path):
    create_conf(tmp_path, ["sphinx_qt_documentation"])
    create_index(tmp_path)
    # subprocess.check_call(["sphinx-build", str(tmp_path), str(tmp_path / "html")])
    assert build_main([str(tmp_path), str(tmp_path / "html")]) == 0
    with open(tmp_path / "html" / "index.html") as f_p:
        text = f_p.read()
    assert 'href="https://doc.qt.io/qt-6/qwidget.html' in text


@pytest.mark.parametrize(
    "target,url",
    [
        ("Qt5", "https://doc.qt.io/qt-5/qwidget.html"),
        ("PySide2", "https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QWidget.html"),
        (
            "PyQt5",
            "https://www.riverbankcomputing.com/static/Docs/PyQt5/api/qtwidgets/qwidget.html",
        ),
        ("Qt6", "https://doc.qt.io/qt-6/qwidget.html"),
        ("PySide6", "https://doc.qt.io/qtforpython/PySide6/QtWidgets/QWidget.html"),
        (
            "PyQt6",
            "https://www.riverbankcomputing.com/static/Docs/PyQt6/api/qtwidgets/qwidget.html",
        ),
    ],
)
def test_target_documentation(tmp_path, target, url):
    qt_doc = f'qt_documentation = "{target}"'
    create_conf(tmp_path, ["sphinx_qt_documentation"], qt_doc)
    create_index(tmp_path)
    # subprocess.check_call(["sphinx-build", str(tmp_path), str(tmp_path / "html")])
    assert build_main([str(tmp_path), str(tmp_path / "html")]) == 0
    with open(tmp_path / "html" / "index.html") as f_p:
        text = f_p.read()
    assert 'href="' + url in text


@pytest.mark.parametrize(
    "target,url",
    [
        ("Qt6", "https://doc.qt.io/qtforpython-6/"),
        ("Qt6", "https://www.riverbankcomputing.com/static/Docs/PyQt6/"),
        ("Qt5", "https://doc.qt.io/qtforpython-5/"),
        ("Qt5", "https://www.riverbankcomputing.com/static/Docs/PyQt5/"),
        ("Qt", "https://doc.qt.io/qtforpython-6/"),
        ("Qt", "https://www.riverbankcomputing.com/static/Docs/PyQt6/"),
        ("PySide2", "https://doc.qt.io/qtforpython-5/"),
        ("PyQt5", "https://www.riverbankcomputing.com/static/Docs/PyQt5/"),
        ("PySide6", "https://doc.qt.io/qtforpython-6/"),
        ("PyQt6", "https://www.riverbankcomputing.com/static/Docs/PyQt6/"),
    ],
)
def test_different_sources(tmp_path, target, url):
    qt_doc = f'intersphinx_mapping = {{"{target}": ("{url}", None) }}'
    create_conf(tmp_path, ["sphinx_qt_documentation"], qt_doc)
    create_index(tmp_path)
    # subprocess.check_call(["sphinx-build", str(tmp_path), str(tmp_path / "html")])
    assert build_main([str(tmp_path), str(tmp_path / "html")]) == 0
    with open(tmp_path / "html" / "index.html") as f_p:
        text = f_p.read()
    assert 'href="https://doc.qt.io/qt-6/qwidget.html"' in text


CONF_TEMPLATE = """
project = 'sphinx-qt-documentation-test01'
extensions = {}
master_doc = "index"

{}
"""

INDEX_TEMPLATE = """
Welcome to sphinx-qt-documentation-test01's documentation!
==========================================================

Please show me some :py:class:`QWidget` classes.

Please show me some :py:meth:`QWidget.rect` method.

"""
