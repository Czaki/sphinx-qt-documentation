"""
This module contains sphinx extension supporting for build PartSeg documentation.

this extension provides one configuration option:

`qt_documentation` with possible values:

 * PyQt5 - linking to PyQt documentation on https://www.riverbankcomputing.com/static/Docs/PyQt5/api/ (incomplete)
 * Qt5 - linking to Qt5 documentation on "https://doc.qt.io/qt-5/" (default)
 * PySide2 - linking to PySide2 documentation on  "https://doc.qt.io/qtforpython/PySide2/"
"""
import importlib
import inspect
import re

from sphinx.application import Sphinx
from sphinx.config import ENUM
from sphinx.environment import BuildEnvironment
from docutils.nodes import Element, TextElement
from docutils import nodes
from typing import List, Optional, Dict, Any
from sphinx.locale import get_translation
from sphinx.ext.intersphinx import InventoryAdapter

_ = get_translation("sphinx")


def _get_signal_and_version():
    name_mapping = { 'qtpy': (lambda: 'QT_VERSION', 'Signal'),
                     'Qt': (lambda: '__qt_version__', 'Signal'),
                     'PySide2': (lambda: importlib.import_module('PySide2.QtCore').__version__, 'Signal'),
                     'PyQt5': (lambda: importlib.import_module('PyQt5.QtCore').QT_VERSION_STR, 'pyqtSignal')}
    for module_name, (version, signal_name) in name_mapping.items():
        try:
            core = importlib.import_module(f'{module_name}.QtCore')
            signal = getattr(core, signal_name)
            return signal, version()
        except (ModuleNotFoundError, ImportError):
            continue
    raise RuntimeError('No Qt bindings found')


Signal, QT_VERSION = _get_signal_and_version()

# TODO add response to
#  https://stackoverflow.com/questions/47102004/how-to-properly-link-to-pyqt5-documentation-using-intersphinx

signal_slot_uri = {
    "Qt5": "https://doc.qt.io/qt-5/signalsandslots.html",
    "PySide2": "https://doc.qt.io/qtforpython/overviews/signalsandslots.html",
    "PyQt5": "https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html",
}

signal_name = {"Qt5": "Signal", "PySide2": "Signal", "PyQt5": "pyqtSignal"}

slot_name = {"Qt5": "Slot", "PySide2": "Slot", "PyQt5": "pyqtSlot"}

type_translate_dict = {
    "class": ["class", "enum", "attribute"],
    "meth": ["method", "signal"],
    "mod": ["module"],
}

signal_pattern = re.compile(r"((\w+\d?\.QtCore\.)|(QtCore\.)|(\.))?(pyqt)?Signal")
slot_pattern = re.compile(r"((\w+\d?\.QtCore\.)|(QtCore\.)|(\.))?(pyqt)?Slot")


# noinspection PyUnusedLocal
def missing_reference(
    app: Sphinx, env: BuildEnvironment, node: Element, contnode: TextElement
) -> Optional[nodes.reference]:
    """Linking to Qt documentation."""
    target: str = node["reftarget"]
    inventories = InventoryAdapter(env)
    objtypes: Optional[List[str]] = None
    if node["reftype"] == "any":
        # we search anything!
        objtypes = [
            "%s:%s" % (domain.name, objtype)
            for domain in env.domains.values()
            for objtype in domain.object_types
        ]
        domain = None
    else:
        domain = node.get("refdomain")
        if not domain:
            # only objects in domains are in the inventory
            return None
        objtypes = env.get_domain(domain).objtypes_for_role(node["reftype"])
        if not objtypes:
            return None
        objtypes = ["%s:%s" % (domain, objtype) for objtype in objtypes]
    if signal_pattern.match(target):
        uri = signal_slot_uri[app.config.qt_documentation]
        dispname = signal_name[app.config.qt_documentation]
        version = QT_VERSION
    elif slot_pattern.match(target):
        uri = signal_slot_uri[app.config.qt_documentation]
        dispname = slot_name[app.config.qt_documentation]
        version = QT_VERSION
    else:
        target_list = [target, *['.'.join([prefix, target]) for prefix in ["PyQt5", "PySide2"]]]
        target_list += ['.'.join([*target.split('.')[:2], target]) for target in target_list]
        target_list += [target[:-1] for target in target_list if target[-1] == 's']
        if node.get("reftype") in type_translate_dict:
            type_names = type_translate_dict[node.get("reftype")]
        else:
            type_names = [node.get("reftype")]
        for name in type_names:
            for preprefix in ["sip", "py"]:
                obj_type_name = "{}:{}".format(preprefix, name)
                if obj_type_name in inventories.named_inventory["Qt"]:
                    break
            else:
                continue
            for target_name in target_list:
                if target_name in inventories.main_inventory[obj_type_name]:
                    d = inventories.named_inventory["Qt"][obj_type_name]
                    if target_name not in d:
                        continue
                    proj, version, uri, dispname = d[target_name]
                    if dispname in ['', '-']:
                        dispname = target
                    uri = uri.replace("##", "#")
                    #  print(node)  # print nodes with unresolved references
                    break
            else:
                continue
            break
        else:
            return None
        if app.config.qt_documentation == "Qt5":
            html_name = uri.split("/")[-1]
            uri = "https://doc.qt.io/qt-5/" + html_name
            if name == 'enum':
                uri += "-enum"

    # remove this line if you would like straight to pyqt documentation
    if version:
        reftitle = _("(in %s v%s)") % (app.config.qt_documentation, version)
    else:
        reftitle = _("(in %s)") % (app.config.qt_documentation,)
    newnode = nodes.reference("", "", internal=False, refuri=uri, reftitle=reftitle)
    dispname_start, sep, rest = dispname.partition('.')
    if dispname_start in ["PyQt5", "PySide2"]:
        dispname = rest
    if node.get("refexplicit"):
        # use whatever title was given
        newnode.append(contnode)
    else:
        # else use the given display name (used for :ref:)
        newnode.append(contnode.__class__(dispname, dispname))
    return newnode


re.compile(r" +algorithm_changed *= *Signal(\([^)]*\))")


# noinspection PyUnusedLocal
def autodoc_process_signature(
    app: Sphinx, what, name: str, obj, options, signature, return_annotation
):
    if isinstance(obj, Signal):
        module_name, class_name, signal_name_local = name.rsplit(".", 2)
        module = importlib.import_module(module_name)
        class_ob = getattr(module, class_name)
        reg = re.compile(r" +" + signal_name_local + r" *= *Signal(\([^)]*\))")
        match = reg.findall(inspect.getsource(class_ob))
        if match:
            return match[0], None

        pos = len(name.rsplit(".", 1)[1])
        return ", ".join([sig[pos:] for sig in obj.signatures]), None


def setup(app: Sphinx) -> Dict[str, Any]:
    app.setup_extension("sphinx.ext.intersphinx")
    if hasattr(app.config, "intersphinx_mapping"):
        if "PyQt5" not in app.config.intersphinx_mapping:
            app.config.intersphinx_mapping["PyQt5"] = (
                "https://www.riverbankcomputing.com/static/Docs/PyQt5",
                None,
            )
    else:
        app.config.intersphinx_mapping = {
            "PyQt5": ("https://www.riverbankcomputing.com/static/Docs/PyQt5", None)
        }
    app.connect("missing-reference", missing_reference)
    app.connect("autodoc-process-signature", autodoc_process_signature)
    # app.connect('doctree-read', doctree_read)
    app.add_config_value("qt_documentation", "Qt5", True, ENUM("Qt5", "PySide2", "PyQt5"))
    return {"version": "0.1", "env_version": 1, "parallel_read_safe": True}


# https://doc.qt.io/qtforpython/PySide2/QtWidgets/QListWidget.html#PySide2.QtWidgets.QListWidget.itemDoubleClicked
# https://doc.qt.io/qtforpython/PySide2/QtWidgets/QListWidget.html#
# PySide2.QtWidgets.PySide2.QtWidgets.QListWidget.itemDoubleClicked
