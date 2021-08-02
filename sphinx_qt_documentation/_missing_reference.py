"""
implementation of sphinx missing_reference hook
"""

import importlib
import inspect
import re
from typing import Optional, Tuple

from docutils import nodes
from docutils.nodes import Element, TextElement
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.ext.intersphinx import InventoryAdapter
from sphinx.locale import get_translation

_ = get_translation("sphinx")


def _get_signal_and_version():
    name_mapping = {
        "qtpy": (lambda: "QT_VERSION", "Signal"),
        "Qt": (lambda: "__qt_version__", "Signal"),
        "PySide2": (
            lambda: importlib.import_module("PySide2.QtCore").__version__,
            "Signal",
        ),
        "PyQt5": (
            lambda: importlib.import_module("PyQt5.QtCore").QT_VERSION_STR,
            "pyqtSignal",
        ),
    }
    for module_name, (version, signal_name) in name_mapping.items():
        try:
            core = importlib.import_module(f"{module_name}.QtCore")
            signal = getattr(core, signal_name)
            return signal, version()  # pylint: disable=E1102
        except ImportError:
            continue
    raise RuntimeError("No Qt bindings found")


Signal, QT_VERSION = _get_signal_and_version()

signal_slot_uri = {
    "Qt5": "https://doc.qt.io/qt-5/signalsandslots.html",
    "PySide2": "https://doc.qt.io/qtforpython/overviews/signalsandslots.html",
    "PyQt5": "https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html",
}
signal_name_dict = {"Qt5": "Signal", "PySide2": "Signal", "PyQt5": "pyqtSignal"}
slot_name = {"Qt5": "Slot", "PySide2": "Slot", "PyQt5": "pyqtSlot"}
type_translate_dict = {
    "class": ["class", "enum", "attribute"],
    "meth": ["method", "signal"],
    "mod": ["module"],
}
signal_pattern = re.compile(r"((\w+\d?\.QtCore\.)|(QtCore\.)|(\.))?(pyqt)?Signal")
slot_pattern = re.compile(r"((\w+\d?\.QtCore\.)|(QtCore\.)|(\.))?(pyqt)?Slot")


def _fix_target(target: str, inventories: InventoryAdapter) -> str:
    if (
        target.startswith("PySide2")
        and "PySide2" not in inventories.named_inventory
        and "PyQt5" in inventories.named_inventory
    ):
        _head, dot, tail = target.partition(".")
        return "PyQt5" + dot + tail
    if (
        target.startswith("PyQt5")
        and "PyQt5" not in inventories.named_inventory
        and "PySide2" in inventories.named_inventory
    ):
        _head, dot, tail = target.partition(".")
        return "PySide2" + dot + tail
    return target


def _get_inventory_for_target(target: str, inventories: InventoryAdapter):
    prefix = target.partition(".")[0]
    if prefix in {"PySide2", "PyQt5"} and prefix in inventories.named_inventory:
        return inventories.named_inventory[prefix]
    if "Qt" in inventories.named_inventory:
        return inventories.named_inventory["Qt"]
    if "Qt5" in inventories.named_inventory:
        return inventories.named_inventory["Qt5"]
    if "PyQt5" in inventories.named_inventory:
        return inventories.named_inventory["PyQt5"]
    return inventories.named_inventory["PySide2"]


def _extract_from_inventory(target: str, inventory, node: Element):
    target_list = [target, "PyQt5." + target, "PySide2." + target]
    if "sip:module" in inventory:
        target_list += [name + "." + target for name in inventory["sip:module"].keys()]
    if "py:module" in inventory:
        target_list += [name + "." + target for name in inventory["py:module"].keys()]
        target_list += [
            name + "." + name + "." + target for name in inventory["py:module"].keys()
        ]
    type_names = type_translate_dict.get(node.get("reftype"), [node.get("reftype")])
    for name in type_names:
        for prefix in ["sip", "py"]:
            obj_type_name = f"{prefix}:{name}"
            if obj_type_name in inventory:
                break
        else:
            continue
        for target_name in target_list:
            if target_name in inventory[obj_type_name]:
                _proj, version, uri, display_name = inventory[obj_type_name][
                    target_name
                ]
                if display_name in ["", "-"]:
                    display_name = target
                uri = uri.replace("##", "#")
                return uri, display_name, version, target_name, name
    return None


def _parse_pyside_uri(uri: str) -> Tuple[str, str]:
    """
    Try to parse PySide URI and extract html file name and anchor
    """
    uri_re = re.compile(
        r"https://doc.qt.io/qtforpython(-5)?/(?P<path>(PySide[26])(/\w+)+)\.html#(?P<anchor>(\w+\.)+(\w+))"
    )
    matched = uri_re.match(uri)
    if matched is None:
        raise ValueError(f"Cannot parse '{uri}' uri")
    path = matched.group("path")
    uri_anchor = matched.group("anchor")
    class_string = path.split("/")[-1]
    anchor = "" if uri_anchor.endswith(class_string) else uri_anchor.split(".")[-1]
    return class_string.lower() + ".html", anchor


def _prepare_object(
    target: str, inventories: InventoryAdapter, node: Element, app: Sphinx
) -> Optional[Tuple[str, str, str]]:
    inventory = _get_inventory_for_target(target, inventories)

    res = _extract_from_inventory(target, inventory, node)
    if res is None:
        return None

    uri, display_name, version, target_name, name = res
    if app.config.qt_documentation == "Qt5":
        if "riverbankcomputing" in uri:
            html_name = uri.split("/")[-1]
            uri = "https://doc.qt.io/qt-5/" + html_name
            if name == "enum":
                uri += "-enum"
        else:
            # PySide2 documentation
            html_name, anchor = _parse_pyside_uri(uri)
            uri = (
                "https://doc.qt.io/qt-5/" + html_name + ("#" + anchor if anchor else "")
            )
    elif app.config.qt_documentation == "PySide2" and "PySide2" not in uri:
        if node.get("reftype") == "meth":
            split_tup = target_name.split(".")[1:]
            ref_name = ".".join(["PySide2", split_tup[0], "PySide2"] + split_tup)
            html_name = "/".join(split_tup[:-1]) + ".html#" + ref_name
        else:
            html_name = "/".join(target_name.split(".")[1:]) + ".html"
        uri = "https://doc.qt.io/qtforpython/PySide2/" + html_name
    return uri, display_name, version


# noinspection PyUnusedLocal
# pylint: disable=W0613
def missing_reference(
    app: Sphinx, env: BuildEnvironment, node: Element, contnode: TextElement
) -> Optional[nodes.reference]:
    """Linking to Qt documentation."""
    target: str = node["reftarget"]
    inventories = InventoryAdapter(env)
    if node["reftype"] == "any":
        # we search anything!
        domain = None
    else:
        domain = node.get("refdomain")
        if not domain:
            # only objects in domains are in the inventory
            return None
        if not env.get_domain(domain).objtypes_for_role(node["reftype"]):
            return None
    new_target = _fix_target(target, inventories)
    if signal_pattern.match(new_target):
        uri = signal_slot_uri[app.config.qt_documentation]
        version = QT_VERSION
        display_name = signal_name_dict[app.config.qt_documentation]
    elif slot_pattern.match(new_target):
        uri = signal_slot_uri[app.config.qt_documentation]
        version = QT_VERSION
        display_name = slot_name[app.config.qt_documentation]
    else:
        resp = _prepare_object(new_target, inventories, node, app)
        if resp is None:
            return None
        uri, display_name, version = resp
    # remove this line if you would like straight to pyqt documentation
    if version:
        reftitle = _("(in %s v%s)") % (app.config.qt_documentation, version)
    else:
        reftitle = _("(in %s)") % (app.config.qt_documentation,)
    newnode = nodes.reference("", "", internal=False, refuri=uri, reftitle=reftitle)
    if node.get("refexplicit"):
        # use whatever title was given
        newnode.append(contnode)
    else:
        # else use the given display name (used for :ref:)
        newnode.append(contnode.__class__(display_name, display_name))
    return newnode


# noinspection PyUnusedLocal
# pylint: disable=W0613,R0913
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
        return ", ".join(sig[pos:] for sig in obj.signatures), None
    return None