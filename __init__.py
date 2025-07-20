import array
import bpy
import re
from bpy_extras import anim_utils


class SHAPEKEYMIMIC_PT_ToolPanel(bpy.types.Panel):
    bl_idname = "SHAPEKEYMIMIC_PT_tool_panel"
    bl_label = "ShapeKey Mimic"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object

        box = layout.box()
        box.label(text="Shape Keys:")

        if obj and obj.data.shape_keys:
            key_blocks = obj.data.shape_keys.key_blocks
            for idx, key in enumerate(key_blocks):
                row = box.row()
                is_active = (obj.active_shape_key_index == idx)
                icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                op = row.operator("shapekeymimic.set_active_shapekey", text="", icon=icon, emboss=False)
                op.target_index = idx
                row.label(text=key.name)
                row.prop(key, "value", text="")
        else:
            box.label(text="No shape keys found", icon='ERROR')

        col = layout.column(align=True)
        col.prop(scene, "shapekeymimic_overwrite", text="Overwrite")
        col.operator("shapekeymimic.copy_shapekey", text="Copy Shape Key", icon="SHAPEKEY_DATA")
        col.operator("shapekeymimic.copy_keyframe", text="Copy Keyframe", icon="ANIM")


class SHAPEKEYMIMIC_OT_SetActiveShapekey(bpy.types.Operator):
    bl_idname = "shapekeymimic.set_active_shapekey"
    bl_label = "Set Active Shape Key"
    bl_description = "Set the selected shape key as active"

    target_index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.active_object
        if obj and obj.data.shape_keys:
            obj.active_shape_key_index = self.target_index
            return {'FINISHED'}
        return {'CANCELLED'}


class SHAPEKEYMIMIC_OT_CopyShapeKey(bpy.types.Operator):
    bl_idname = "shapekeymimic.copy_shapekey"
    bl_label = "Copy Shape Key"
    bl_description = "Copy the active shape key from the active object to selected target objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'ERROR'}, "Switch to Object mode.")
            return {'CANCELLED'}

        selected = context.selected_objects
        source = context.active_object
        targets = [obj for obj in selected if obj != source]

        if len(selected) < 2:
            self.report({'ERROR'}, "Select source and target objects.")
            return {'CANCELLED'}

        if source is None or source.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}

        if source.data.shape_keys is None:
            self.report({'ERROR'}, "No shape keys on source.")
            return {'CANCELLED'}

        active_key = source.active_shape_key
        if not active_key:
            self.report({'ERROR'}, "Select a shape key.")
            return {'CANCELLED'}

        if active_key.name == "Basis":
            self.report({'ERROR'}, "Cannot copy 'Basis' shape key.")
            return {'CANCELLED'}

        if active_key.mute:
            self.report({'ERROR'}, "Unmute the shape key.")
            return {'CANCELLED'}

        overwrite = context.scene.shapekeymimic_overwrite
        active_key_name = active_key.name
        active_key_value = active_key.value

        active_key.value = 1.0
        context.view_layer.update()
        source_coords = [v.co.copy() for v in active_key.data]

        copied_count = 0
        skipped_count = 0

        for target in targets:
            if target.type != 'MESH':
                continue

            if not target.data.shape_keys:
                target.shape_key_add(name="Basis", from_mix=False)

            exists = active_key_name in target.data.shape_keys.key_blocks

            try:
                if exists:
                    if overwrite:
                        target_key = target.data.shape_keys.key_blocks[active_key_name]
                    else:
                        skipped_count += 1
                        raise ValueError("Shape key exists. Skipped.")
                else:
                    target_key = target.shape_key_add(name=active_key_name, from_mix=False)

                if len(target_key.data) != len(source_coords):
                    raise ValueError("Vertex count mismatch.")

                for i, v in enumerate(target_key.data):
                    v.co = source_coords[i]

                target_key.value = active_key_value
                copied_count += 1

            except Exception as e:
                self.report({'WARNING'}, f"[{target.name}] {str(e)}")

        active_key.value = active_key_value

        self.report({'INFO'}, f"Copied: {copied_count}, Skipped: {skipped_count}")
        return {'FINISHED'}


class SHAPEKEYMIMIC_OT_CopyKeyframe(bpy.types.Operator):
    bl_idname = "shapekeymimic.copy_keyframe"
    bl_label = "Copy Shape Key Keyframe"
    bl_description = "Copy shape key keyframes from active source object to selected target objects"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def _copy_keyframes_from_to(source_fc, target_fc):
        target_fc.keyframe_points.clear()
        for kp in source_fc.keyframe_points:
            new_kp = target_fc.keyframe_points.insert(kp.co.x, kp.co.y, options={'FAST'})
            new_kp.interpolation = kp.interpolation
            new_kp.easing = kp.easing

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'ERROR'}, "Switch to Object mode.")
            return {'CANCELLED'}

        selected = context.selected_objects
        source = context.active_object
        targets = [obj for obj in selected if obj != source]

        if len(selected) < 2:
            self.report({'ERROR'}, "Select source and target objects.")
            return {'CANCELLED'}

        if source is None or source.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}

        active_key = source.active_shape_key
        if not active_key:
            self.report({'ERROR'}, "Select a shape key.")
            return {'CANCELLED'}

        if active_key.name == "Basis":
            self.report({'ERROR'}, "Cannot copy 'Basis' shape key.")
            return {'CANCELLED'}

        if active_key.mute:
            self.report({'ERROR'}, "Unmute the shape key.")
            return {'CANCELLED'}

        if not bpy.data.actions:
            self.report({'ERROR'}, "No actions found.")
            return {'CANCELLED'}

        overwrite = context.scene.shapekeymimic_overwrite
        active_key_name = active_key.name

        shape_keys = source.data.shape_keys
        anim_data = shape_keys.animation_data
        if not anim_data or not anim_data.action or not anim_data.action_slot:
            self.report({'ERROR'}, "No shape key animation data.")
            return {'CANCELLED'}

        try:
            src_cb = anim_utils.action_get_channelbag_for_slot(anim_data.action, anim_data.action_slot)
        except Exception as e:
            self.report({'WARNING'}, f"Channel bag error: {str(e)}")
            return {'CANCELLED'}

        if not src_cb:
            self.report({'ERROR'}, "No channel bag found for source action.")
            return {'CANCELLED'}

        src_fc = None
        for fcurve in src_cb.fcurves:
            match = re.match(r'key_blocks\["(.+?)"\]\.value', fcurve.data_path)
            if match:
                key_name = match.group(1)
                if key_name == active_key_name:
                    src_fc = fcurve
                    break
            else:
                continue

        if not src_fc:
            self.report({'ERROR'}, f"No keyframe found for shape key '{active_key_name}'.")
            return {'CANCELLED'}    
        
        for target in targets:
            if target.type != 'MESH':
                continue

            tgt_keys = target.data.shape_keys
            if tgt_keys is None:
                continue

            tgt_anim_data =  target.animation_data
            tgt_sk_anim_data = tgt_keys.animation_data
            if tgt_sk_anim_data and tgt_sk_anim_data.action:
                tgt_action = tgt_sk_anim_data.action
            else:
                if tgt_anim_data and tgt_anim_data.action:
                    tgt_action = tgt_anim_data.action
                else:
                    tgt_action = bpy.data.actions.new(name=f"{target.name}Action")

            if tgt_sk_anim_data and tgt_sk_anim_data.action_slot:
                tgt_slot = tgt_sk_anim_data.action_slot
            else:
                tgt_slot = tgt_action.slots.new("KEY", active_key_name)

            if not tgt_action.layers:
                tgt_strip = tgt_action.layers.new(anim_data.action_slot.target_id_type).strips.new(type="KEYFRAME")
            else:
                tgt_strip = tgt_action.layers[0].strips[0]

            tgt_cb = tgt_strip.channelbag(tgt_slot, ensure=True)

            path = src_fc.data_path
            index = src_fc.array_index
            tgt_fc = tgt_cb.fcurves.find(path, index=index)
            if overwrite:
                tgt_fc = tgt_cb.fcurves.new(path, index=index)
            else:
                if not tgt_fc:
                    tgt_fc = tgt_cb.fcurves.new(path, index=index)
                else:
                    self.report({'WARNING'}, f"Keyframe for '{active_key_name}' already exists in {target.name}. Skipped.")
                    continue

            self._copy_keyframes_from_to(src_fc, tgt_fc)

            adt = tgt_keys.animation_data_create()
            adt.action = tgt_action
            adt.action_slot = tgt_slot

        return {'FINISHED'}


classes = (
    SHAPEKEYMIMIC_PT_ToolPanel,
    SHAPEKEYMIMIC_OT_CopyShapeKey,
    SHAPEKEYMIMIC_OT_SetActiveShapekey,
    SHAPEKEYMIMIC_OT_CopyKeyframe,
)


def register():
    bpy.types.Scene.shapekeymimic_overwrite = bpy.props.BoolProperty(
        name="Overwrite Existing Shape Keys",
        description="Overwrite shape keys with the same name.",
        default=False
    )
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.shapekeymimic_overwrite


if __name__ == "__main__":
    register()