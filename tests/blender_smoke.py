"""Exercise real Blender operations against an isolated factory-startup scene."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import bpy

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "ptool", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
)
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)
addon.register()


class Reporter:
    def report(self, level, message):
        print(level, message)


reporter = Reporter()
bpy.ops.object.select_all(action="DESELECT")
cube = bpy.data.objects["Cube"]
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
with tempfile.TemporaryDirectory(prefix="ptool-test-") as directory:
    root = Path(directory)
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "shot.blend"))
    bpy.context.scene.ptool.artist_initials = "AB"
    (root / "__versionning").mkdir()
    (root / "__versionning" / "README.txt").write_text("Not a version")
    first = addon.P_Save.save(reporter)
    second = addon.P_Save.save(reporter)
    assert first.name == "shot_001_AB.blend" and second.name == "shot_002_AB.blend"
    assert first.exists() and second.exists()
    assert Path(bpy.data.filepath).name == "shot.blend"
    addon.P_Name.Set_Name("asset_obj")
    assert cube.name == "asset_obj" and cube.data.name == "asset_msh"
    addon.P_Name.Prefix("SM_")
    assert cube.name == "SM_asset_obj"
    addon.P_Name.rename_type(reporter)
    cube.location = (4, 2, 1)
    addon.P_Modeling.move_to_origin(reporter)
    assert tuple(cube.matrix_world.translation) == (0, 0, 0)
    addon.P_Export.export_mesh(reporter, str(root / "exports"))
    assert len(list((root / "exports").glob("*.fbx"))) == 1
    assert bpy.context.selected_objects == [cube]
    try:
        addon.P_Export.export_mesh(reporter, str(root / "exports"))
        raise AssertionError("Existing export overwritten")
    except ValueError:
        pass
    try:
        addon.P_Export.export_anim(reporter, str(root / "animation"))
        raise AssertionError("Missing armature accepted")
    except ValueError:
        pass
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.armature_add()
    rig = bpy.context.object
    rig.name = "test_rig"
    rig.keyframe_insert(data_path="location", frame=1)
    rig.location.x = 1
    rig.keyframe_insert(data_path="location", frame=2)
    addon.P_Export.export_anim(reporter, str(root / "rig_export"))
    assert (root / "rig_export" / "test_rig.fbx").stat().st_size > 100
    bpy.ops.object.select_all(action="DESELECT")
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    empty_group = cube.vertex_groups.new(name="unused")
    weighted = cube.vertex_groups.new(name="tiny-but-valid-weight")
    weighted.add([0], 0.001, "REPLACE")
    addon.P_Clean.remove_unused_vertex_group(reporter)
    assert cube.vertex_groups.get("unused") is None
    assert cube.vertex_groups.get("tiny-but-valid-weight") is not None
    unused_material = bpy.data.materials.new("Keep unrelated material")
    addon.P_Clean.clean_selected_mesh(reporter)
    assert bpy.data.materials.get(unused_material.name) is not None
    addon.P_Clean.remove_unused_materials(reporter)
    addon.P_Clean.display_tri(reporter)
    addon.P_Clean.display_ngon(reporter)
    bpy.ops.object.select_all(action="DESELECT")
    empty = bpy.data.objects.new("Artist empty", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.select_set(True)
    bpy.context.view_layer.objects.active = empty
    addon.P_Name.Set_Name("control")
    addon.P_Name.Prefix("rig_")
    addon.P_Name.Suffix("_empty")
    addon.P_Link.import_selected_linked(reporter)
    assert bpy.data.objects.get("rig_control_empty") is not None
    source_collection = bpy.data.collections.new("Library asset")
    source_object = bpy.data.objects.new("Library mesh", cube.data.copy())
    source_collection.objects.link(source_object)
    library_path = root / "library.blend"
    bpy.data.libraries.write(str(library_path), {source_collection})
    with bpy.data.libraries.load(str(library_path), link=True) as (source, target):
        target.collections = ["Library asset"]
    instance = bpy.data.objects.new("Linked instance", None)
    instance.instance_type = "COLLECTION"
    instance.instance_collection = target.collections[0]
    bpy.context.scene.collection.objects.link(instance)
    bpy.ops.object.select_all(action="DESELECT")
    instance.select_set(True)
    bpy.context.view_layer.objects.active = instance
    addon.P_Link.import_selected_linked(reporter)
    assert instance.instance_type == "NONE"
    assert any(child.type == "MESH" and child.library is None for child in instance.children)
    assert bpy.data.objects.get("rig_control_empty") is not None
    try:
        addon.P_Screenshot.take(reporter, str(root / "screenshots"))
        raise AssertionError("Background viewport capture accepted")
    except ValueError:
        pass
addon.unregister()
assert not hasattr(bpy.types.Scene, "ptool")
addon.register()
addon.unregister()
print("PTOOL_SMOKE_OK", bpy.app.version_string)
