"""Real viewport regression; run Blender without --background in a disposable scene."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import bpy

ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("P_TOOL_TEST_ADDON_ROOT", ROOT))
spec = importlib.util.spec_from_file_location(
    "p_tool", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
)
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)


def run():
    try:
        addon.register()
        window = bpy.context.window
        area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
        region = next(region for region in area.regions if region.type == "WINDOW")
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.object.select_all(action="DESELECT")
            cube = bpy.data.objects["Cube"]
            bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0))
            sphere = bpy.context.object
            cube.select_set(True)
            bpy.context.view_layer.objects.active = cube
            bpy.data.objects["Light"].hide_set(True)
            render = bpy.context.scene.render
            render.resolution_x = render.resolution_y = 64
            render.resolution_percentage = 100
            render.image_settings.file_format = "JPEG"
            render.filepath = "//original-output"
            area.spaces.active.overlay.show_overlays = True
            expected_selection = {cube.name, sphere.name}
            expected_visibility = {
                obj.name: obj.hide_get() for obj in bpy.context.view_layer.objects
            }

            def assert_restored():
                assert {obj.name for obj in bpy.context.selected_objects} == expected_selection
                assert bpy.context.view_layer.objects.active == cube
                assert {
                    obj.name: obj.hide_get() for obj in bpy.context.view_layer.objects
                } == expected_visibility
                assert area.spaces.active.overlay.show_overlays
                assert render.image_settings.file_format == "JPEG"
                assert render.filepath == "//original-output"

            operator = SimpleNamespace(report=lambda *_: None)
            with tempfile.TemporaryDirectory(prefix="p-tool-viewport-") as directory:
                addon.P_Screenshot.take(operator, directory)
                images = list(Path(directory).glob("*.png"))
                assert len(images) == 2, images
                assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in images)
                assert_restored()
                try:
                    addon.P_Screenshot.take(operator, directory)
                    raise AssertionError("Existing capture was overwritten")
                except ValueError as exc:
                    assert "already exists" in str(exc)
                assert_restored()

            def fail_render(**kwargs):
                raise RuntimeError("Injected render failure")

            proxy = SimpleNamespace(
                context=bpy.context,
                app=bpy.app,
                ops=SimpleNamespace(
                    object=bpy.ops.object, render=SimpleNamespace(opengl=fail_render)
                ),
            )
            with tempfile.TemporaryDirectory(prefix="p-tool-failure-") as directory:
                with patch.object(addon.P_Screenshot, "bpy", proxy):
                    try:
                        addon.P_Screenshot.take(operator, directory)
                        raise AssertionError("Expected render failure")
                    except RuntimeError as exc:
                        assert "Injected render failure" in str(exc)
                assert_restored()
        addon.unregister()
        print("P_TOOL_VIEWPORT_OK", bpy.app.version_string, flush=True)
        bpy.ops.wm.quit_blender()
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


bpy.app.timers.register(run, first_interval=2.0)
