import bpy
from mathutils import Vector

class ANIM_OT_animate_along_curve(bpy.types.Operator):
    """Animate selected object along a chosen curve"""
    bl_idname = "anim.animate_along_curve"
    bl_label = "Animate Along Curve"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        # Check if we have both an active object and a target curve
        return (context.active_object is not None and 
                context.scene.aac_target_curve is not None and 
                context.scene.aac_target_curve.type == 'CURVE')

    def execute(self, context):
        obj = context.active_object
        curve = context.scene.aac_target_curve
        start_frame = context.scene.aac_start_frame
        end_frame = context.scene.aac_end_frame
        auto_orient = context.scene.aac_auto_orient
        
        if not obj:
            self.report({'ERROR'}, "No active object selected!")
            return {'CANCELLED'}
            
        if not curve or curve.type != 'CURVE':
            self.report({'ERROR'}, "Invalid or no curve selected!")
            return {'CANCELLED'}
            
        if start_frame >= end_frame:
            self.report({'ERROR'}, "End frame must be greater than start frame!")
            return {'CANCELLED'}
            
        try:
            # Remove any existing follow path constraints
            for c in obj.constraints:
                if c.type == 'FOLLOW_PATH':
                    obj.constraints.remove(c)
            
            # Add new follow path constraint
            constraint = obj.constraints.new(type='FOLLOW_PATH')
            constraint.name = "Follow Path"
            constraint.target = curve
            constraint.use_curve_follow = auto_orient
            constraint.forward_axis = 'Y'  # Forward axis (can be made configurable)
            constraint.up_axis = 'Z'       # Up axis (can be made configurable)
            
            # Ensure the curve is properly set up
            curve.data.use_path = True
            curve.data.path_duration = end_frame - start_frame
            
            # Animate the offset factor
            if not obj.animation_data:
                obj.animation_data_create()
                
            # Clear any existing animation on the offset
            fcurves = obj.animation_data.action.fcurves if obj.animation_data.action else None
            if fcurves:
                for fc in fcurves:
                    if fc.data_path == f'constraints["{constraint.name}"].offset_factor':
                        obj.animation_data.action.fcurves.remove(fc)
            
            # Set keyframes for the offset
            constraint.offset_factor = 0.0
            constraint.keyframe_insert(data_path="offset_factor", frame=start_frame)
            
            constraint.offset_factor = 1.0
            constraint.keyframe_insert(data_path="offset_factor", frame=end_frame)
            
            # Set interpolation to linear for smooth motion
            if obj.animation_data.action:
                for fc in obj.animation_data.action.fcurves:
                    if fc.data_path == f'constraints["{constraint.name}"].offset_factor':
                        for kf in fc.keyframe_points:
                            kf.interpolation = 'LINEAR'
            
            # Update the viewport
            context.view_layer.update()
            
            self.report({'INFO'}, "Successfully applied curve animation!")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error applying curve animation: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        if not context.scene.aac_target_curve:
            self.report({'ERROR'}, "Please select a target curve first!")
            return {'CANCELLED'}
        return self.execute(context)

def menu_func(self, context):
    self.layout.operator(ANIM_OT_animate_along_curve.bl_idname)

def register():
    bpy.utils.register_class(ANIM_OT_animate_along_curve)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ANIM_OT_animate_along_curve)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
