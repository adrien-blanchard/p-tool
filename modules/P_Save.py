"""Incremented .blend copies without changing the working file."""

from pathlib import Path
import re
import bpy
from .common import open_directory


def version_directory():
    if not bpy.data.is_saved:
        raise ValueError("Save the .blend file before creating a version.")
    return Path(bpy.data.filepath).parent / "__versionning"


def save(operator):
    directory = version_directory()
    directory.mkdir(parents=True, exist_ok=True)
    source = Path(bpy.data.filepath)
    initials = bpy.context.scene.ptool.artist_initials.strip().upper()
    if initials and not re.fullmatch(r"[A-Z0-9]{1,12}", initials):
        raise ValueError("Artist initials must contain 1-12 letters or digits.")
    pattern = re.compile(r"^" + re.escape(source.stem) + r"_(\d+)(?:_[A-Za-z0-9]+)?\.blend$")
    numbers = [
        int(match.group(1))
        for path in directory.iterdir()
        if (match := pattern.fullmatch(path.name))
    ]
    number = max(numbers, default=0) + 1
    suffix = "_" + initials if initials else ""
    destination = directory / f"{source.stem}_{number:03}{suffix}.blend"
    if destination.exists():
        raise ValueError("That version already exists; try again.")
    result = bpy.ops.wm.save_as_mainfile(filepath=str(destination), copy=True, check_existing=True)
    if "FINISHED" not in result:
        raise RuntimeError("Blender did not finish saving the version.")
    operator.report({"INFO"}, f"Saved {destination.name}")
    return destination


def open():
    open_directory(version_directory())
