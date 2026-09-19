"""Selected FBX exports with validated paths and selection restoration."""

import bpy
from .common import (
    check_destinations,
    output_directory,
    preserve_selection,
    require_object_mode,
    safe_name,
    open_directory,
)


def export_mesh(operator, export_path):
    require_object_mode()
    objects = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    if not objects:
        raise ValueError("Select at least one mesh.")
    directory = output_directory(export_path)
    paths = [directory / (safe_name(obj.name) + ".fbx") for obj in objects]
    check_destinations(paths)
    with preserve_selection():
        for obj, path in zip(objects, paths):
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            result = bpy.ops.export_scene.fbx(
                filepath=str(path),
                use_selection=True,
                object_types={"MESH"},
                apply_unit_scale=False,
                apply_scale_options="FBX_SCALE_NONE",
                axis_forward="-Z",
                axis_up="Y",
                bake_space_transform=True,
                mesh_smooth_type="FACE",
                bake_anim=False,
            )
            if "FINISHED" not in result:
                raise RuntimeError(
                    f"Export failed for {obj.name}. Earlier exports may already exist."
                )
    operator.report({"INFO"}, f"Exported {len(paths)} mesh(es).")


def export_anim(operator, export_path):
    require_object_mode()
    rigs = [obj for obj in bpy.context.selected_objects if obj.type == "ARMATURE"]
    if len(rigs) != 1:
        raise ValueError("Select exactly one armature, together with its meshes.")
    directory = output_directory(export_path)
    path = directory / (safe_name(rigs[0].name) + ".fbx")
    check_destinations([path])
    result = bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Z",
        axis_up="Y",
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim_use_nla_strips=False,
    )
    if "FINISHED" not in result:
        raise RuntimeError("Blender did not finish the animation export.")
    operator.report({"INFO"}, "Animation exported.")


def open(path):
    open_directory(output_directory(path))
