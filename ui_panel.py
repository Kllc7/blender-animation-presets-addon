import bpy
from bpy.props import EnumProperty, PointerProperty, IntProperty, BoolProperty

class ANIM_PT_MainPanel(bpy.types.Panel):
    """Main Panel for Animation Presets and Curve Animation"""
    bl_label = "Animation Presets"
    bl_idname = "ANIM_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animation"

    def draw(self, context):
        layout = self.layout
        
        # Animation Presets Section
        box = layout.box()
        row = box.row()
        row.label(text="Animation Presets", icon='ANIM')
        
        # Grid layout for presets
        grid = box.grid_flow(row_major=True, columns=2, align=True)
        
        # Get presets from animation_presets.py
        from . import animation_presets
        presets = animation_presets.get_presets()
        
        for preset in presets:
            col = grid.column(align=True)
            col.template_icon(icon_value=preset.get("preview_icon", 0))
            op = col.operator("anim.apply_preset", text=preset["name"])
            op.preset_id = preset["id"]
            col.label(text=preset["description"])
        
        # Animate Along Curve Section
        box = layout.box()
        row = box.row()
        row.label(text="Animate Along Curve", icon='CURVE_DATA')
        
        col = box.column(align=True)
        col.prop_search(context.scene, "aac_target_curve", context.scene, "objects", text="Target Curve")
        col.prop(context.scene, "aac_start_frame", text="Start Frame")
        col.prop(context.scene, "aac_end_frame", text="End Frame")
        col.prop(context.scene, "aac_auto_orient", text="Auto Orient")
        
        # Preview section
        preview_box = box.box()
        preview_box.label(text="Preview", icon='RENDER_ANIMATION')
        preview_box.template_icon(icon_value=0)  # Will be replaced with actual preview
        
        # Apply button
        col = box.column(align=True)
        col.scale_y = 1.5
        col.operator("anim.animate_along_curve", text="Apply Curve Animation", icon='PLAY')

def register():
    bpy.types.Scene.aac_target_curve = PointerProperty(
        name="Target Curve",
        type=bpy.types.Object,
        description="Select the curve for object animation"
    )
    bpy.types.Scene.aac_start_frame = IntProperty(
        name="Start Frame",
        default=1,
        min=1,
        description="Animation Start Frame"
    )
    bpy.types.Scene.aac_end_frame = IntProperty(
        name="End Frame",
        default=250,
        min=1,
        description="Animation End Frame"
    )
    bpy.types.Scene.aac_auto_orient = BoolProperty(
        name="Auto Orient",
        default=True,
        description="Automatically orient along the curve"
    )
    
    bpy.utils.register_class(ANIM_PT_MainPanel)

def unregister():
    del bpy.types.Scene.aac_target_curve
    del bpy.types.Scene.aac_start_frame
    del bpy.types.Scene.aac_end_frame
    del bpy.types.Scene.aac_auto_orient
    
    bpy.utils.unregister_class(ANIM_PT_MainPanel)
