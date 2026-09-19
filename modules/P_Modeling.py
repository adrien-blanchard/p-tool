"""Small modeling helpers; no hidden scene-wide cleanup."""

import bpy
from .common import require_object_mode


def move_to_origin(operator):
    require_object_mode()
    objects = list(bpy.context.selected_objects)
    if not objects:
        raise ValueError("Select at least one object.")
    if any(obj.library for obj in objects):
        raise ValueError("Make linked objects local first.")
    for obj in objects:
        matrix = obj.matrix_world.copy()
        matrix.translation = (0, 0, 0)
        obj.matrix_world = matrix
    operator.report({"INFO"}, "Selected objects moved to world origin.")


def set_origin(operator):
    if (
        bpy.context.mode != "EDIT_MESH"
        or bpy.context.area is None
        or bpy.context.area.type != "VIEW_3D"
    ):
        raise ValueError("Select mesh vertices in Edit Mode in a 3D View first.")
    import bmesh

    if not any(
        vertex.select for vertex in bmesh.from_edit_mesh(bpy.context.edit_object.data).verts
    ):
        raise ValueError("Select at least one vertex.")
    cursor = bpy.context.scene.cursor.location.copy()
    try:
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    finally:
        bpy.context.scene.cursor.location = cursor
        if bpy.context.mode == "OBJECT":
            bpy.ops.object.mode_set(mode="EDIT")
    operator.report({"INFO"}, "Origin moved to the selected vertices.")
