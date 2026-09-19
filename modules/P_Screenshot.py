"""Viewport PNG captures, restoring all visibility and selection state."""

import bpy
from .common import (
    check_destinations,
    output_directory,
    preserve_selection,
    require_object_mode,
    safe_name,
    open_directory,
)


def take(operator, screenshot_path):
    require_object_mode()
    context = bpy.context
    if bpy.app.background or context.area is None or context.area.type != "VIEW_3D":
        raise ValueError("Capture requires an interactive 3D View.")
    objects = list(context.selected_objects)
    if not objects:
        raise ValueError("Select at least one object.")
    directory = output_directory(screenshot_path)
    paths = [directory / (safe_name(obj.name) + ".png") for obj in objects]
    check_destinations(paths)
    overlay = context.space_data.overlay.show_overlays
    visibility = [(obj, obj.hide_get()) for obj in context.view_layer.objects]
    render = context.scene.render
    old_format = render.image_settings.file_format
    old_filepath = render.filepath
    try:
        with preserve_selection():
            context.space_data.overlay.show_overlays = False
            render.image_settings.file_format = "PNG"
            for selected, path in zip(objects, paths):
                for obj, _hidden in visibility:
                    obj.hide_set(obj != selected)
                bpy.ops.object.select_all(action="DESELECT")
                selected.select_set(True)
                render.filepath = str(path)
                bpy.ops.render.opengl(write_still=True, view_context=True)
    finally:
        for obj, hidden in visibility:
            obj.hide_set(hidden)
        context.space_data.overlay.show_overlays = overlay
        render.image_settings.file_format = old_format
        render.filepath = old_filepath
    operator.report({"INFO"}, f"Saved {len(paths)} viewport capture(s).")


def open(path):
    open_directory(output_directory(path))
