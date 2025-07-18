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

        # 쉐이프 키 리스트
        box = layout.box()
        box.label(text="Shape Keys:")

        if obj and obj.data.shape_keys:
            shape_keys = obj.data.shape_keys
            key_blocks = shape_keys.key_blocks

            # 선택 가능한 리스트로 출력
            for idx, key in enumerate(key_blocks):
                row = box.row()
                is_active = (obj.active_shape_key_index == idx)
                icon = 'RADIOBUT_ON' if is_active else 'RADIOBUT_OFF'
                op = row.operator("shapekeymimic.set_active_shapekey", text="", icon=icon, emboss=False)
                op.target_index = idx
                row.label(text=key.name)
                row.prop(key, "value", text="")  # 슬라이더

        else:
            box.label(text="No shape keys found", icon='ERROR')

        col = layout.column(align=True)
        col.prop(context.scene, "shapekeymimic_overwrite", text="Overwrite")
        col.operator("shapekeymimic.copy_shapekey", text="Copy Shape key", icon="SHAPEKEY_DATA")
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
    bl_label = "Copy Shapekey"
    bl_description = "Copy the active shape key from the active object to selected target objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            self.report({'ERROR'}, "Operator must be run in Object mode.")
            return {'CANCELLED'}

        selected = context.selected_objects
        source = context.active_object
        targets = [obj for obj in selected if obj != source]

        if len(selected) < 2:
            self.report({'ERROR'}, "Select at least one source and one target object.")
            return {'CANCELLED'}

        if source is None or source.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}

        if source.data.shape_keys is None:
            self.report({'ERROR'}, "Source object has no shape keys.")
            return {'CANCELLED'}

        active_key = source.active_shape_key
        if not active_key:
            self.report({'ERROR'}, "No active shape key selected.")
            return {'CANCELLED'}

        if active_key.name == "Basis":
            self.report({'ERROR'}, "'Basis' shape key cannot be copied.")
            return {'CANCELLED'}

        if active_key.mute:
            self.report({'ERROR'}, "Muted shape key cannot be copied.")
            return {'CANCELLED'}

        overwrite = context.scene.shapekeymimic_overwrite
        active_key_name = active_key.name
        active_key_value = active_key.value

        # Ensure the key is applied
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

            is_conflict = active_key_name in target.data.shape_keys.key_blocks

            try:
                if is_conflict:
                    if overwrite:
                        target_key = target.data.shape_keys.key_blocks[active_key_name]
                    else:
                        skipped_count += 1
                        raise ValueError("Shape key already exists and overwrite is disabled.")
                else:
                    target_key = target.shape_key_add(name=active_key_name, from_mix=False)

                if len(target_key.data) != len(source_coords):
                    raise ValueError("Vertex count mismatch between source and target.")

                for i, v in enumerate(target_key.data):
                    v.co = source_coords[i]

                target_key.value = active_key_value
                copied_count += 1

            except Exception as e:
                self.report({'WARNING'}, f"[{target.name}] {str(e)}")

        # Restore original key value
        active_key.value = active_key_value

        self.report({'INFO'}, f"Copied: {copied_count}, Skipped: {skipped_count}")
        return {'FINISHED'}


class SHAPEKEYMIMIC_OT_CopyKeyframe(bpy.types.Operator):
    bl_idname = "shapekeymimic.copy_keyframe"
    bl_label = "Copy Shapekey keyframe"
    bl_description = "Copy shapekey keyframe from active source object to the selected target objects"
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
            self.report({'ERROR'}, "Operator must be run in Object mode.")
            return {'CANCELLED'}

        selected = context.selected_objects
        source = context.active_object
        targets = [obj for obj in selected if obj != source]

        if len(selected) < 2:
            self.report({'ERROR'}, "Select at least one source and one target object.")
            return {'CANCELLED'}

        if source is None or source.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}

        active_key = source.active_shape_key
        if not active_key:
            self.report({'ERROR'}, "No active shape key selected.")
            return {'CANCELLED'}

        if active_key.name == "Basis":
            self.report({'ERROR'}, "'Basis' shape key cannot be copied.")
            return {'CANCELLED'}

        if active_key.mute:
            self.report({'ERROR'}, "Muted shape key cannot be copied.")
            return {'CANCELLED'}

        # Global action container
        g_actions = bpy.data.actions
        if len(g_actions) < 1:
            self.report({'ERROR'}, "No actions found")
            return {'CANCELLED'}

        src_action = source.data.shape_keys.animation_data.action
        src_action_slot = source.data.shape_keys.animation_data.action_slot
        # Action slot based on shape key
        if src_action is None or src_action_slot is None:
            self.report({'ERROR'}, "Source object has no shape key based animation data.")
            return {'CANCELLED'}

        overwrite = context.scene.shapekeymimic_overwrite

        active_key_name = active_key.name

        try:
            src_cb = anim_utils.action_get_channelbag_for_slot(src_action, src_action_slot)
        except Exception as e:
            self.report({'WARNING'}, f"Failed to get a channel bag from source {str(e)}")
            return {'CANCELLED'}

        for target in targets:
            if target.type != 'MESH':
                continue

            tgt_name = target.name
            tgt_type = target.id_type
            tgt_key = target.data.shape_keys
            if tgt_key is None:
                continue
            
            # bpy.context.active_object.animation_data는 객체가 어떻게 움직이고, 회전하고, 크기를 조절하거나 자신의 속성을 변경하는지를 다룹니다.
            # bpy.context.active_object.data.shape_keys.animation_data는 쉐이프 키의 영향을 통해 객체의 모양이 시간이 지남에 따라 어떻게 변형되는지를 다룹니다.

            # 향후 검토 필요 지점
            # 기존 액션에 추가 혹은 새로운 액션으로 추가?
            # 새로운 액션으로 추가시 NLA 에디터에서 수동으로 병합가능
            # 현재는 기존 액션에 바로 channelbag 추가 방식으로 진행
            tgt_animation_data = target.animation_data
            if not tgt_animation_data is None:
                tgt_action = tgt_animation_data.action
            else:
                action_name = f"{tgt_name}Action"
                tgt_action = bpy.data.actions.new(name=action_name)
            
            # object-based action != shape key-based action
            if not tgt_key.animation_data is None:
                tgt_slot = target.data.shape_keys.animation_data.action_slot
            else:
                tgt_slot = tgt_action.slots.new("KEY", active_key_name)

            if len(tgt_action.layers) < 1:
                tgt_strip = tgt_action.layers.new(src_action_slot.target_id_type).strips.new(type="KEYFRAME")
            else:
                # one action can have only on layer up to now (Blender 4.5)
                # one layer can have only one strip up to now (Blender 4.5)
                layer = tgt_action.layers[0]
                tgt_strip = layer.strips[0]

            tgt_cb = tgt_strip.channelbag(tgt_slot, ensure=True)

            for fc in src_cb.fcurves:
                pattern = rf'key_blocks\["{re.escape(active_key_name)}"\]\.value'
                match = re.search(pattern, fc.data_path)
                if not match:
                    self.report({'WARNING'}, "No matched channel to the name of the shape key")
                    continue

                path = fc.data_path
                index = fc.array_index
                tgt_fc = tgt_cb.fcurves.find(path, index=index)
                if not tgt_fc:
                    tgt_fc = tgt_cb.fcurves.new(path, index=index)

                self._copy_keyframes_from_to(fc, tgt_fc)

            adt = tgt_key.animation_data_create()
            adt.action = tgt_action
            adt.action_slot = tgt_slot

        return {'FINISHED'}


def register():
    # 애드온 등록
    bpy.types.Scene.shapekeymimic_overwrite = bpy.props.BoolProperty(
        name="Overwrite Existing Shape Keys",
        description="Ignore conflicting caused by sharing the same name.",
        default=False
    )
    bpy.utils.register_class(SHAPEKEYMIMIC_PT_ToolPanel)
    bpy.utils.register_class(SHAPEKEYMIMIC_OT_CopyShapeKey)
    bpy.utils.register_class(SHAPEKEYMIMIC_OT_SetActiveShapekey)
    bpy.utils.register_class(SHAPEKEYMIMIC_OT_CopyKeyframe)


def unregister():
    # 애드온 제거
    del bpy.types.Scene.shapekeymimic_overwrite
    bpy.utils.unregister_class(SHAPEKEYMIMIC_PT_ToolPanel)
    bpy.utils.unregister_class(SHAPEKEYMIMIC_OT_CopyShapeKey)
    bpy.utils.unregister_class(SHAPEKEYMIMIC_OT_SetActiveShapekey)
    bpy.utils.unregister_class(SHAPEKEYMIMIC_OT_CopyKeyframe)


if __name__ == "__main__":
    register()