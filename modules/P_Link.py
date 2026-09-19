"""Localize selected links without deleting ordinary empties or purging data."""

import bpy
from .common import preserve_selection, require_object_mode


def _localize(objects, operator):
    require_object_mode()
    if not objects:
        raise ValueError("Select linked objects or collection instances first.")
    with preserve_selection():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        instances = [
            obj for obj in objects if obj.instance_type == "COLLECTION" and obj.instance_collection
        ]
        bpy.ops.object.duplicates_make_real(use_base_parent=True, use_hierarchy=True)
        bpy.ops.object.make_local(type="SELECT_OBDATA_MATERIAL")
        # Keep each instance empty as a transform parent. Never remove scene empties.
        for obj in instances:
            if obj.library is None:
                obj.instance_type = "NONE"
    operator.report({"INFO"}, "Links localized. Original empty parents retained.")


def import_selected_linked(operator):
    _localize(list(bpy.context.selected_objects), operator)


def import_all_linked(operator):
    objects = [
        obj
        for obj in bpy.context.view_layer.objects
        if obj.visible_get() and (obj.library or obj.instance_type == "COLLECTION")
    ]
    _localize(objects, operator)
