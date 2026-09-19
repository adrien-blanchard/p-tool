"""Small safety helpers shared by the Blender operators."""

from contextlib import contextmanager
from pathlib import Path
import re
import subprocess
import sys

import bpy


def selected_meshes():
    return [
        obj
        for obj in bpy.context.selected_objects
        if obj.type == "MESH" and obj.library is None and obj.data.library is None
    ]


def require_object_mode():
    if bpy.context.mode != "OBJECT":
        raise ValueError("Switch to Object Mode first.")


def output_directory(value):
    if not value.strip():
        raise ValueError("Choose an output folder first.")
    path = Path(bpy.path.abspath(value)).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_name(value):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    if not name or name.split(".")[0].upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        name = "object_" + name
    return name


def check_destinations(paths):
    if len({str(path).casefold() for path in paths}) != len(paths):
        raise ValueError("Object names resolve to the same output filename. Rename them first.")
    for path in paths:
        if path.exists():
            raise ValueError(
                f"Output already exists: {path.name}. Choose another folder or rename the object."
            )


def open_directory(path):
    path = Path(path).resolve()
    if not path.is_dir():
        raise ValueError("The folder does not exist yet.")
    if sys.platform == "win32":
        import os

        os.startfile(str(path))
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


@contextmanager
def preserve_selection():
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    try:
        yield
    finally:
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        for obj in selected:
            if obj.name in bpy.context.view_layer.objects:
                obj.select_set(True)
        if active and active.name in bpy.context.view_layer.objects:
            bpy.context.view_layer.objects.active = active
