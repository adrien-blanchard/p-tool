# SPDX-License-Identifier: GPL-3.0-or-later
"""P-Tool: the original TOTB Blender pipeline toolkit, maintained for current Blender."""

bl_info = {
    "name": "P-Tool",
    "author": "TOTB, Adrien Blanchard",
    "description": "Everyday pipeline helpers for Blender",
    "blender": (3, 6, 0),
    "version": (1, 1, 0),
    "location": "3D View > Sidebar > P-Tool",
    "doc_url": "https://github.com/adrien-blanchard/p-tool",
    "tracker_url": "https://github.com/adrien-blanchard/p-tool/issues",
    "category": "Object",
}

import bpy
from .modules import P_Save, P_Name, P_Export, P_Modeling, P_Link, P_Clean, P_Screenshot


class PToolProperties(bpy.types.PropertyGroup):
    artist_initials: bpy.props.StringProperty(
        name="Initials", description="Optional initials on versioned copies", maxlen=12
    )
    export_path: bpy.props.StringProperty(name="Folder", subtype="DIR_PATH")
    screenshot_path: bpy.props.StringProperty(name="Folder", subtype="DIR_PATH")


ACTIONS = {
    "SAVE": lambda op, ctx: P_Save.save(op),
    "OPEN_VERSIONS": lambda op, ctx: P_Save.open(),
    "ORIGIN": lambda op, ctx: P_Modeling.move_to_origin(op),
    "VERTEX_ORIGIN": lambda op, ctx: P_Modeling.set_origin(op),
    "EXPORT_MESH": lambda op, ctx: P_Export.export_mesh(op, ctx.scene.ptool.export_path),
    "EXPORT_ANIM": lambda op, ctx: P_Export.export_anim(op, ctx.scene.ptool.export_path),
    "OPEN_EXPORT": lambda op, ctx: P_Export.open(ctx.scene.ptool.export_path),
    "SCREENSHOT": lambda op, ctx: P_Screenshot.take(op, ctx.scene.ptool.screenshot_path),
    "OPEN_SCREENSHOTS": lambda op, ctx: P_Screenshot.open(ctx.scene.ptool.screenshot_path),
    "CLEAN_NAMES": lambda op, ctx: P_Name.clean_name(op),
    "TYPE_NAMES": lambda op, ctx: P_Name.rename_type(op),
    "LINK_SELECTED": lambda op, ctx: P_Link.import_selected_linked(op),
    "LINK_ALL": lambda op, ctx: P_Link.import_all_linked(op),
    "CLEAN_GROUPS": lambda op, ctx: P_Clean.remove_unused_vertex_group(op),
    "CLEAN_MATERIALS": lambda op, ctx: P_Clean.remove_unused_materials(op),
    "CLEAN_MESH": lambda op, ctx: P_Clean.clean_selected_mesh(op),
    "TRIANGLES": lambda op, ctx: P_Clean.display_tri(op),
    "NGONS": lambda op, ctx: P_Clean.display_ngon(op),
}


class PTOOL_OT_action(bpy.types.Operator):
    bl_idname = "ptool.action"
    bl_label = "P-Tool"
    bl_options = {"REGISTER", "UNDO"}
    action: bpy.props.StringProperty()

    def execute(self, context):
        callback = ACTIONS.get(self.action)
        if callback is None:
            self.report({"ERROR"}, "Unknown P-Tool action.")
            return {"CANCELLED"}
        try:
            callback(self, context)
        except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


class PTOOL_OT_name(bpy.types.Operator):
    bl_idname = "ptool.name"
    bl_label = "P-Name"
    bl_options = {"REGISTER", "UNDO"}
    value: bpy.props.StringProperty(name="Name")
    operation: bpy.props.EnumProperty(
        items=[
            ("RENAME", "Rename", ""),
            ("PREFIX", "Prefix", ""),
            ("SUFFIX", "Suffix", ""),
        ]
    )

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def invoke(self, context, event):
        self.value = context.active_object.name if context.active_object else ""
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        try:
            {
                "RENAME": P_Name.Set_Name,
                "PREFIX": P_Name.Prefix,
                "SUFFIX": P_Name.Suffix,
            }[self.operation](self.value)
        except (ValueError, RuntimeError) as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


def button(layout, action, label, icon="NONE"):
    layout.operator("ptool.action", text=label, icon=icon).action = action


class PTOOL_PT_main(bpy.types.Panel):
    bl_label = "P-Tool"
    bl_idname = "PTOOL_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "P-Tool"

    def draw(self, context):
        self.layout.label(text="Everyday pipeline helpers")


class _SubPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "P-Tool"
    bl_parent_id = "PTOOL_PT_main"
    bl_options = {"DEFAULT_CLOSED"}


class PTOOL_PT_save(_SubPanel, bpy.types.Panel):
    bl_label = "P-Save"
    bl_idname = "PTOOL_PT_save"

    def draw(self, context):
        layout = self.layout
        if not bpy.data.is_saved:
            layout.label(text="Save your .blend file first.", icon="INFO")
            layout.operator("wm.save_as_mainfile")
        else:
            layout.prop(context.scene.ptool, "artist_initials")
            button(layout, "SAVE", "Save incremented copy", "FILE_TICK")
            button(layout, "OPEN_VERSIONS", "Open versions", "FILE_FOLDER")


class PTOOL_PT_modeling(_SubPanel, bpy.types.Panel):
    bl_label = "P-Modeling"
    bl_idname = "PTOOL_PT_modeling"

    def draw(self, context):
        button(self.layout, "ORIGIN", "Move to world origin", "WORLD")
        button(self.layout, "VERTEX_ORIGIN", "Origin to selected vertices", "OBJECT_ORIGIN")


class PTOOL_PT_screenshot(_SubPanel, bpy.types.Panel):
    bl_label = "P-Screenshot"
    bl_idname = "PTOOL_PT_screenshot"

    def draw(self, context):
        self.layout.prop(context.scene.ptool, "screenshot_path")
        button(self.layout, "SCREENSHOT", "Capture selected objects", "RENDER_STILL")
        button(self.layout, "OPEN_SCREENSHOTS", "Open captures", "FILE_FOLDER")


class PTOOL_PT_export(_SubPanel, bpy.types.Panel):
    bl_label = "P-Export"
    bl_idname = "PTOOL_PT_export"

    def draw(self, context):
        self.layout.prop(context.scene.ptool, "export_path")
        button(self.layout, "EXPORT_MESH", "Meshes to separate FBX files", "EXPORT")
        button(self.layout, "EXPORT_ANIM", "Armature + animation to FBX", "ARMATURE_DATA")
        button(self.layout, "OPEN_EXPORT", "Open exports", "FILE_FOLDER")


class PTOOL_PT_name(_SubPanel, bpy.types.Panel):
    bl_label = "P-Name"
    bl_idname = "PTOOL_PT_name"

    def draw(self, context):
        self.layout.operator(
            "ptool.name", text="Rename / Prefix / Suffix", icon="OUTLINER_DATA_FONT"
        )
        button(self.layout, "CLEAN_NAMES", "Clean selected names")
        button(self.layout, "TYPE_NAMES", "Prefix selected by type")


class PTOOL_PT_link(_SubPanel, bpy.types.Panel):
    bl_label = "P-Link"
    bl_idname = "PTOOL_PT_link"

    def draw(self, context):
        button(self.layout, "LINK_SELECTED", "Make selected links local", "UNLINKED")
        button(self.layout, "LINK_ALL", "Make visible links local", "UNLINKED")


class PTOOL_PT_clean(_SubPanel, bpy.types.Panel):
    bl_label = "P-Clean"
    bl_idname = "PTOOL_PT_clean"

    def draw(self, context):
        self.layout.label(text="Selected meshes only", icon="INFO")
        button(self.layout, "CLEAN_GROUPS", "Remove empty vertex groups")
        button(self.layout, "CLEAN_MATERIALS", "Remove unused material slots")
        button(self.layout, "CLEAN_MESH", "Merge doubles / clean loose vertices")
        row = self.layout.row(align=True)
        button(row, "TRIANGLES", "Select triangles")
        button(row, "NGONS", "Select ngons")


CLASSES = (
    PToolProperties,
    PTOOL_OT_action,
    PTOOL_OT_name,
    PTOOL_PT_main,
    PTOOL_PT_save,
    PTOOL_PT_modeling,
    PTOOL_PT_screenshot,
    PTOOL_PT_export,
    PTOOL_PT_name,
    PTOOL_PT_link,
    PTOOL_PT_clean,
)
addon_keymaps = []


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ptool = bpy.props.PointerProperty(type=PToolProperties)
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig:
        keymap = keyconfig.keymaps.new(name="Window")
        item = keymap.keymap_items.new("ptool.action", type="S", value="PRESS", ctrl=True, alt=True)
        item.properties.action = "SAVE"
        addon_keymaps.append((keymap, item))
        keymap = keyconfig.keymaps.new(name="Object Mode")
        item = keymap.keymap_items.new("ptool.name", type="F2", value="PRESS", alt=True)
        addon_keymaps.append((keymap, item))


def unregister():
    for keymap, item in addon_keymaps:
        keymap.keymap_items.remove(item)
    addon_keymaps.clear()
    del bpy.types.Scene.ptool
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
