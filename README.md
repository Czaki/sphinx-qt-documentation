# Sphinx Qt documentation 

This is plugin to add cross link to qt documentation for python code created with PyQt5 or PySide2.

Currently it support `qtpy`, `Qt.py` wrappers and `PyQt5` and `PySide2`.

This extension provides one configuration option:

`qt_documentation` with possible values:

* PyQt5 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt5/api/ (incomplete)
* Qt5 - linking to Qt5 documentation on "https://doc.qt.io/qt-5/" (default)
* PySide2 - linking to PySide2 documentation on  "https://doc.qt.io/qtforpython/PySide2/"

For default this extension use `inv` file from PyQt5 to resolve objects. 
to overwrite this behaviour set another url for `intersphinx_mapping[PyQt5]` ex.:

```python
intersphinx_mapping = {...
                       "PyQt5": (custom_url, None),
                       ...}
```
