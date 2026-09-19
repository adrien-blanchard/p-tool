"""Selection-scoped cleanup. Never purge unrelated datablocks."""

import bmesh
import bpy
from .common import require_object_mode, selected_meshes, preserve_selection


def _meshes():
    require_object_mode()
    meshes = selected_meshes()
    if not meshes:
        raise ValueError("Select an editable mesh first.")
    if any(obj.data.users > 1 for obj in meshes):
        raise ValueError("Make shared mesh data single-user before cleanup.")
    return meshes


def remove_unused_vertex_group(operator):
    count = 0
    for obj in _meshes():
        used = {
            item.group for vertex in obj.data.vertices for item in vertex.groups if item.weight > 0
        }
        # Empty groups referenced by a modifier may intentionally be masks.
        referenced = {
            getattr(modifier, prop.identifier)
            for modifier in obj.modifiers
            for prop in modifier.bl_rna.properties
            if prop.type == "STRING" and "vertex_group" in prop.identifier
        }
        for group in reversed(list(obj.vertex_groups)):
            if group.index not in used and group.name not in referenced:
                obj.vertex_groups.remove(group)
                count += 1
    operator.report({"INFO"}, f"Removed {count} empty vertex group(s).")


def remove_unused_materials(operator):
    for obj in _meshes():
        used = {polygon.material_index for polygon in obj.data.polygons}
        for index in reversed(range(len(obj.data.materials))):
            if index not in used:
                obj.data.materials.pop(index=index)
    operator.report({"INFO"}, "Removed unused material slots from selected meshes.")


def clean_selected_mesh(operator):
    for obj in _meshes():
        mesh = bmesh.new()
        try:
            mesh.from_mesh(obj.data)
            bmesh.ops.remove_doubles(mesh, verts=list(mesh.verts), dist=0.0001)
            loose = [vertex for vertex in mesh.verts if not vertex.link_edges]
            if loose:
                bmesh.ops.delete(mesh, geom=loose, context="VERTS")
            bmesh.ops.recalc_face_normals(mesh, faces=list(mesh.faces))
            mesh.to_mesh(obj.data)
            obj.data.update()
        finally:
            mesh.free()
    operator.report({"INFO"}, "Selected meshes cleaned.")


def _display(operator, ngon):
    meshes = _meshes()
    count = 0
    with preserve_selection():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            for polygon in obj.data.polygons:
                polygon.select = len(polygon.vertices) > 4 if ngon else len(polygon.vertices) == 3
                count += int(polygon.select)
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
    # Face selection is visible when the artist enters Edit Mode.
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
    operator.report(
        {"INFO"},
        f"{count} {'ngon(s)' if ngon else 'triangle(s)'} selected; enter Edit Mode to inspect.",
    )
    return count


def display_tri(operator):
    return _display(operator, False)


def display_ngon(operator):
    return _display(operator, True)
