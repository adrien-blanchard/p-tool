"""Rename selected editable objects; Blender resolves object-name collisions."""

import json
from pathlib import Path
import re
import bpy


def _objects():
    objects = list(bpy.context.selected_objects)
    if not objects:
        raise ValueError("Select at least one object.")
    if any(obj.library for obj in objects):
        raise ValueError("Make linked objects local before renaming.")
    return objects


def _data_name(obj):
    if obj.data and obj.data.library is None and obj.data.users == 1:
        obj.data.name = obj.name[:-4] + "_msh" if obj.name.endswith("_obj") else obj.name


def clean_name(operator):
    for obj in _objects():
        obj.name = re.sub(r"\.(\d{3,})$", r"_\1", obj.name)
        _data_name(obj)
    operator.report({"INFO"}, "Selected names cleaned.")


def rename_data(operator):
    for obj in _objects():
        _data_name(obj)


def rename_type(operator):
    path = Path(__file__).resolve().parent.parent / "libraries" / "prefixes.json"
    prefixes = json.loads(path.read_text(encoding="utf-8"))
    for obj in _objects():
        prefix = prefixes.get(obj.type, "")
        if prefix and not obj.name.startswith(prefix):
            obj.name = prefix + obj.name
        _data_name(obj)
    operator.report({"INFO"}, "Selected objects named by type.")


def Set_Name(name):
    objects = _objects()
    name = name.strip()
    if not name:
        raise ValueError("Enter a name first.")
    for index, obj in enumerate(objects, 1):
        if len(objects) == 1:
            obj.name = name
        elif name.endswith("_obj"):
            obj.name = f"{name[:-4]}_{index:03}_obj"
        else:
            obj.name = f"{name}_{index:03}"
        _data_name(obj)


def Prefix(name):
    for obj in _objects():
        obj.name = name + obj.name
        _data_name(obj)


def Suffix(name):
    for obj in _objects():
        obj.name += name
        _data_name(obj)
