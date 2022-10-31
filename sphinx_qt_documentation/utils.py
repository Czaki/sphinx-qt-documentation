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
from sphinx.config import Config
from sphinx.environment import BuildEnvironment
from sphinx.ext.intersphinx import InventoryAdapter
from sphinx.locale import get_translation
from sphinx.util.typing import Inventory

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
        "PySide6": (
            lambda: importlib.import_module("PySide6.QtCore").__version__,
            "Signal",
        ),
        "PyQt6": (
            lambda: importlib.import_module("PyQt6.QtCore").QT_VERSION_STR,
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
SIGNAL_PREFIXES_REGEX = "".join(
    rf"(?:{Signal.__module__.split('.', i)[-1]}\.)?"
    for i in range(len(Signal.__module__.split(".")))
)
signal_slot_uri = {
    "Qt5": "https://doc.qt.io/qt-5/signalsandslots.html",
    "PySide2": "https://doc.qt.io/qtforpython/overviews/signalsandslots.html",
    "PyQt5": "https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html",
    "Qt6": "https://doc.qt.io/qt-6/signalsandslots.html",
    "PySide6": "https://doc.qt.io/qtforpython/overviews/signalsandslots.html",
    "PyQt6": "https://www.riverbankcomputing.com/static/Docs/PyQt6/signals_slots.html",
}
signal_name_dict = {
    "Qt5": "Signal",
    "PySide2": "Signal",
    "PyQt5": "pyqtSignal",
    "Qt6": "Signal",
    "PySide6": "Signal",
    "PyQt6": "pyqtSignal",
}
slot_name = {
    "Qt5": "Slot",
    "PySide2": "Slot",
    "PyQt5": "pyqtSlot",
    "Qt6": "Slot",
    "PySide6": "Slot",
    "PyQt6": "pyqtSlot",
}
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
    if (
        target.startswith("PySide6")
        and "PySide6" not in inventories.named_inventory
        and "PyQt6" in inventories.named_inventory
    ):
        _head, dot, tail = target.partition(".")
        return "PyQt6" + dot + tail
    if (
        target.startswith("PyQt6")
        and "PyQt6" not in inventories.named_inventory
        and "PySide6" in inventories.named_inventory
    ):
        _head, dot, tail = target.partition(".")
        return "PySide6" + dot + tail
    return target


def _get_inventory_for_target(target: str, inventories: InventoryAdapter) -> Inventory:
    name = "PySide6"
    prefix = target.partition(".")[0]
    if (
        prefix in {"PySide2", "PyQt5", "PySide6", "PyQt6"}
        and prefix in inventories.named_inventory
    ):
        name = prefix

    for api in ("Qt", "Qt6", "PyQt6", "PyQt5", "PySide2"):
        if api in inventories.named_inventory:
            name = api
            break
    return inventories.named_inventory[name]


def _extract_from_inventory(target: str, inventory, node: Element):
    target_list = [
        target,
        "PyQt5." + target,
        "PySide2." + target,
        "PyQt6." + target,
        "PySide6." + target,
    ]
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
        r"https://doc.qt.io/qtforpython(-[56])?/(?P<path>(PySide[26])(/\w+)+)\.html#(?P<anchor>(\w+\.)+(\w+))"
    )
    matched = uri_re.match(uri)
    if matched is None:
        raise ValueError(f"Cannot parse '{uri}' uri")
    path = matched.group("path")
    uri_anchor = matched.group("anchor")
    class_string = path.split("/")[-1]
    anchor = "" if uri_anchor.endswith(class_string) else uri_anchor.split(".")[-1]
    return class_string.lower() + ".html", anchor


# pylint: disable=R0912
def _prepare_object(
    target: str, inventories: InventoryAdapter, node: Element, app: Sphinx
) -> Optional[Tuple[str, str, str]]:
    inventory = _get_inventory_for_target(target, inventories)

    res = _extract_from_inventory(target, inventory, node)
    if res is None:
        return None

    uri, display_name, version, target_name, name = res
    if app.config.qt_documentation == "Qt6":
        if "riverbankcomputing" in uri:
            html_name = uri.split("/")[-1]
            uri = "https://doc.qt.io/qt-6/" + html_name
            if name == "enum":
                uri += "-enum"
        else:
            # PySide6 documentation
            html_name, anchor = _parse_pyside_uri(uri)
            uri = (
                "https://doc.qt.io/qt-6/" + html_name + ("#" + anchor if anchor else "")
            )
    elif app.config.qt_documentation == "PySide6" and "PySide6" not in uri:
        if node.get("reftype") == "meth":
            split_tup = target_name.split(".")[1:]
            ref_name = ".".join(["PySide6", split_tup[0], "PySide6"] + split_tup)
            html_name = "/".join(split_tup[:-1]) + ".html#" + ref_name
        else:
            html_name = "/".join(target_name.split(".")[1:]) + ".html"
        uri = "https://doc.qt.io/qtforpython/PySide6/" + html_name
    elif app.config.qt_documentation == "Qt5":
        if "riverbankcomputing" in uri:
            html_name = uri.split("/")[-1]
            uri = "https://doc.qt.io/qt-5/" + html_name
            if name == "enum":
                uri += "-enum"
        else:
            # PySide6 documentation
            html_name, anchor = _parse_pyside_uri(uri)
            uri = (
                "https://doc.qt.io/qt-5/" + html_name + ("#" + anchor if anchor else "")
            )
    elif app.config.qt_documentation == "PySide2" and "PySide2" not in uri:
        if node.get("reftype") == "meth":
            split_tup = target_name.split(".")[1:]
            ref_name = ".".join(["PySide6", split_tup[0], "PySide2"] + split_tup)
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
        reg = re.compile(
            rf" +{signal_name_local} *= *{SIGNAL_PREFIXES_REGEX}Signal(\([^)]*\))"
        )
        match = reg.findall(inspect.getsource(class_ob))
        if match:
            return match[0], None

        pos = len(name.rsplit(".", 1)[1])
        return ", ".join(sig[pos:] for sig in obj.signatures), None
    return None


def patch_intersphinx_mapping(app: Sphinx, config: Config) -> None:
    url_mapping = {
        "PySide6": "https://doc.qt.io/qtforpython",
        "PyQt6": "https://www.riverbankcomputing.com/static/Docs/PyQt6",
        "PySide2": "https://doc.qt.io/qtforpython-5",
        "PyQt5": "https://www.riverbankcomputing.com/static/Docs/PyQt5",
    }

    name = getattr(app.config, "qt_documentation", "Qt6")

    if name == "Qt5":
        name = "PyQt5"
    elif name == "Qt6":
        name = "PyQt6"

    url = url_mapping[name]

    intersphinx_mapping = getattr(app.config, "intersphinx_mapping")
    if intersphinx_mapping is None:
        intersphinx_mapping = {}
    intersphinx_mapping[name] = (name, (url, (None,)))
    app.config.intersphinx_mapping = intersphinx_mapping
