# To get the user-selected assets folder:
# from . import utils
# assets_folder = utils.get_assets_folder()

import bpy # type: ignore
import math
from bpy.types import Panel, Operator, PropertyGroup # type: ignore
from bpy.props import BoolProperty, EnumProperty, IntProperty, FloatProperty, FloatVectorProperty, PointerProperty, StringProperty # type: ignore
from . import utils  # Import utility functions
import os

class ANIM_PG_AnimationPresetProperties(PropertyGroup):
    is_playing: BoolProperty(name="Is Playing", default=False) # type: ignore
    
    def update_start_frame(self, context):
        # Only update if values actually changed
        if (context.scene.frame_current != self.start_frame or 
            context.scene.frame_start != self.start_frame):
            context.scene.frame_current = self.start_frame
            context.scene.frame_start = self.start_frame
    
    # Remove update_speed logic that changes FPS
    start_frame: IntProperty(
        name="Start Frame",
        default=1,
        min=1,
        update=update_start_frame
    ) # type: ignore
    
    animation_speed: FloatProperty(
        name="Animation Speed",
        default=1.0,
        min=0.1,
        max=5.0
    ) # type: ignore
    
    # Curve customization properties
    curve_strength: FloatProperty(name="Curve Strength", default=1.0, min=0.1, max=5.0) # type: ignore
    curve_offset: FloatVectorProperty(name="Curve Offset", default=(0.0, 0.0, 0.0), subtype='TRANSLATION') # type: ignore
    animation_easing: EnumProperty(
        name="Easing",
        items=[
            ('LINEAR', 'Linear', 'Linear interpolation'),
            ('SINE', 'Sine', 'Sinusoidal easing'),
            ('QUAD', 'Quadratic', 'Quadratic easing'),
            ('CUBIC', 'Cubic', 'Cubic easing'),
            ('QUART', 'Quartic', 'Quartic easing'),
            ('QUINT', 'Quintic', 'Quintic easing'),
            ('EXPO', 'Exponential', 'Exponential easing'),
            ('CIRC', 'Circular', 'Circular easing'),
            ('BACK', 'Back', 'Back easing with overshoot'),
            ('BOUNCE', 'Bounce', 'Bounce easing'),
            ('ELASTIC', 'Elastic', 'Elastic easing')
        ],
        default='BACK'
    ) # type: ignore

    preset_enum: EnumProperty(
        name="Preset",
        items=[
            ('PRESET_A', 'Popup Scale', 'Simple pop-up with scale animation'),
            ('PRESET_B', 'Fade In Slide', 'Fade in with slight movement'),
            ('PRESET_C', 'Bouncy Reveal', 'Quick reveal with bouncy scale'),
            ('PRESET_ROTATE_POP', 'Pop-Up + Rotate', 'Pop-up with rotation'),
            ('PRESET_BOUNCE_IN', 'Bounce In', 'Bouncy entrance animation'),
            ('PRESET_SLIDE_FROM_SIDE', 'Slide In', 'Slide in from the side'),
            ('PRESET_FALL_FROM_SKY', 'Fall In', 'Fall from above with bounce'),
            ('PRESET_FLIP_REVEAL', 'Flip Reveal', '3D flip reveal animation'),
            ('PRESET_TYPEWRITER', 'Typewriter', 'Sequential appearance animation'),
            ('PRESET_PULSE', 'Pulse', 'Pulsing scale animation'),
            ('PRESET_ELASTIC', 'Elastic', 'Elastic stretch and squash'),
            ('PRESET_STAGGER', 'Staggered', 'Sequential staggered reveal')
        ],
        default='PRESET_ROTATE_POP'
    ) # type: ignore

    def get_preview_path(self, preset_name):
        addon_dir = os.path.dirname(__file__)
        preview_dir = os.path.join(addon_dir, "previews")
        optimized_dir = os.path.join(preview_dir, "optimized")
        
        # First try to get optimized version
        optimized_path = os.path.join(optimized_dir, f"{preset_name}.mov")
        if os.path.exists(optimized_path):
            return optimized_path
            
        # Fall back to original if optimized doesn't exist
        return os.path.join(preview_dir, f"{preset_name}.mov")

# Function to update playback state
def update_playback_state(self, context):
    if self.is_playing:
        bpy.ops.screen.animation_play()
    else:
        bpy.ops.screen.animation_cancel()

# Function to update easing
def update_easing(self, context):
    # Update easing for selected objects
    for obj in context.selected_objects:
        if obj.animation_data and obj.animation_data.action:
            utils.set_interpolation(obj, self.animation_easing)

# Operators
class ANIM_OT_play_animation(Operator):
    bl_idname = "anim.play_animation"
    bl_label = "Play Animation"
    
    @classmethod
    def poll(cls, context):
        # Only enable if objects are selected
        return bool(context.selected_objects)

    def execute(self, context):
        props = context.scene.animation_preset_props
        props.is_playing = not props.is_playing
        
        # If playing, play the animation in viewport
        if props.is_playing:
            bpy.ops.screen.animation_play()
        else:
            bpy.ops.screen.animation_cancel()
            
        self.report({'INFO'}, f"Playing: {props.is_playing}")
        return {'FINISHED'}

class ANIM_OT_reset_animation(Operator):
    bl_idname = "anim.reset_animation"
    bl_label = "Reset Animation"
    
    @classmethod
    def poll(cls, context):
        # Only enable if objects are selected
        return bool(context.selected_objects)

    def execute(self, context):
        # Set current frame to start frame
        props = context.scene.animation_preset_props
        context.scene.frame_current = props.start_frame
        
        # Clear animation data for selected objects
        for obj in context.selected_objects:
            utils.clear_keyframes(obj)
            
        self.report({'INFO'}, "Animation Reset")
        return {'FINISHED'}

class ANIM_OT_add_preset(Operator):
    bl_idname = "anim.add_preset"
    bl_label = "Apply Preset"
    
    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        props = context.scene.animation_preset_props
        preset = props.preset_enum
        speed = props.animation_speed
        
        # Base duration in frames (will be scaled by speed)
        base_duration = 30
        start_frame = context.scene.frame_current
        
        # Calculate actual duration based on speed
        # Faster speed = shorter duration
        actual_duration = int(base_duration / speed)
        end_frame = start_frame + actual_duration
        
        # Apply the selected preset to all selected objects
        for obj in context.selected_objects:
            # Clear existing animation
            utils.clear_keyframes(obj)
            
            # Apply different animation based on selected preset
            if preset == 'PRESET_A':
                self.apply_popup_scale(obj, start_frame, end_frame)
            elif preset == 'PRESET_B':
                self.apply_fade_slide(obj, start_frame, end_frame)
            elif preset == 'PRESET_C':
                self.apply_bouncy_reveal(obj, start_frame, end_frame)
            elif preset == 'PRESET_ROTATE_POP':
                self.apply_rotate_pop(obj, start_frame, end_frame)
            elif preset == 'PRESET_BOUNCE_IN':
                self.apply_bounce_in(obj, start_frame, end_frame)
            elif preset == 'PRESET_SLIDE_FROM_SIDE':
                self.apply_slide_from_side(obj, start_frame, end_frame)
            elif preset == 'PRESET_FALL_FROM_SKY':
                self.apply_fall_from_sky(obj, start_frame, end_frame)
            elif preset == 'PRESET_FLIP_REVEAL':
                self.apply_flip_reveal(obj, start_frame, end_frame)
            elif preset == 'PRESET_TYPEWRITER':
                self.apply_typewriter(context, obj, start_frame, end_frame)
            elif preset == 'PRESET_PULSE':
                self.apply_pulse(obj, start_frame, end_frame)
            elif preset == 'PRESET_ELASTIC':
                self.apply_elastic(obj, start_frame, end_frame)
            elif preset == 'PRESET_STAGGER':
                self.apply_stagger(context, obj, start_frame, end_frame)
            
            # Set interpolation
            utils.set_interpolation(obj, props.animation_easing)
        
        return {'FINISHED'}
    
    def apply_popup_scale(self, obj, start_frame, end_frame):
        # Define keyframe timing relative to animation duration
        duration = end_frame - start_frame
        
        # Calculate intermediate frames
        frame1 = start_frame
        frame2 = start_frame + int(duration * 0.4)  # Overshoot at 40%
        frame3 = start_frame + int(duration * 0.7)  # Undershoot at 70%
        frame4 = end_frame                          # Final position
        
        # Insert keyframes with easing
        utils.insert_keyframe(obj, "scale", frame1, (0, 0, 0))
        utils.insert_keyframe(obj, "scale", frame2, (1.2, 1.2, 1.2))
        utils.insert_keyframe(obj, "scale", frame3, (0.9, 0.9, 0.9))
        utils.insert_keyframe(obj, "scale", frame4, (1, 1, 1))
        
        # Set interpolation for smooth animation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'SINE'
                    keyframe.easing = 'EASE_IN_OUT'
    
    def apply_fade_slide(self, obj, start_frame, end_frame):
        final_pos = obj.location.copy()
        duration = end_frame - start_frame
        
        # Define keyframes with relative timing for position, scale, and opacity
        keyframes = [
            (0.0, -2.0, 0.0, (0.9, 0.9, 0.9)),    # Start: offset left, invisible, slightly scaled down
            (0.3, -1.0, 0.4, (0.95, 0.95, 0.95)), # Starting to appear
            (0.7, -0.2, 0.8, (1.1, 1.1, 1.1)),    # Almost there, slight overshoot
            (1.0, 0.0, 1.0, (1.0, 1.0, 1.0))      # Final position
        ]
        
        # Apply keyframes with relative timing
        for time_pct, x_offset, alpha, scale in keyframes:
            frame = start_frame + int(duration * time_pct)
            
            # Position keyframe
            pos = (final_pos.x + x_offset, final_pos.y, final_pos.z)
            utils.insert_keyframe(obj, "location", frame, pos)
            
            # Scale keyframe for subtle pop
            utils.insert_keyframe(obj, "scale", frame, scale)
            
            # Fade keyframe
            if obj.material_slots:
                for slot in obj.material_slots:
                    if slot.material and slot.material.use_nodes:
                        for node in slot.material.node_tree.nodes:
                            if node.type == 'BSDF_PRINCIPLED':
                                node.inputs['Alpha'].default_value = alpha
                                node.inputs['Alpha'].keyframe_insert('default_value', frame=frame)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "location":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_OUT'
                elif fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
                
                # Set material alpha interpolation if it exists
                elif "Alpha" in fcurve.data_path:
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN'
    
    def apply_bouncy_reveal(self, obj, start_frame, end_frame):
        duration = end_frame - start_frame
        
        # Define keyframes with relative timing for scale and rotation
        keyframes = [
            (0.0, (0.0, 0.0, 0.0), (0, 0, 0)),         # Start: invisible
            (0.3, (1.3, 1.3, 1.3), (0, 0, 15)),        # First overshoot with slight rotation
            (0.5, (0.7, 0.7, 0.7), (0, 0, -10)),       # First undershoot with counter-rotation
            (0.7, (1.1, 1.1, 1.1), (0, 0, 5)),         # Second overshoot
            (0.85, (0.9, 0.9, 0.9), (0, 0, -2)),       # Second undershoot
            (1.0, (1.0, 1.0, 1.0), (0, 0, 0))          # Final position
        ]
        
        # Store original rotation
        orig_rot = obj.rotation_euler.copy()
        
        # Apply keyframes with relative timing
        for time_pct, scale, rot_offset in keyframes:
            frame = start_frame + int(duration * time_pct)
            
            # Scale keyframe
            utils.insert_keyframe(obj, "scale", frame, scale)
            
            # Rotation keyframe (add offset to original rotation)
            rot = (
                orig_rot[0],
                orig_rot[1],
                orig_rot[2] + math.radians(rot_offset[2])
            )
            utils.insert_keyframe(obj, "rotation_euler", frame, rot)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'ELASTIC'
                        keyframe.easing = 'EASE_OUT'
                elif fcurve.data_path == "rotation_euler":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
    
    def apply_rotate_pop(self, obj, start_frame, end_frame):
        start_rot = obj.rotation_euler.copy()
        duration = end_frame - start_frame
        
        # Define keyframes with relative timing for both rotation and scale
        keyframes = [
            (0.0, 0, (0.0, 0.0, 0.0)),      # Start: invisible
            (0.2, 90, (0.8, 0.8, 0.8)),     # Quarter turn, starting to appear
            (0.5, 270, (1.2, 1.2, 1.2)),    # Three-quarter turn, overshoot scale
            (0.7, 330, (0.9, 0.9, 0.9)),    # Nearly complete, slight undershoot
            (1.0, 360, (1.0, 1.0, 1.0))     # Final position
        ]
        
        # Apply keyframes with relative timing
        for time_pct, angle, scale in keyframes:
            frame = start_frame + int(duration * time_pct)
            # Rotation keyframe
            rot = (
                start_rot[0],
                start_rot[1],
                start_rot[2] + math.radians(angle)
            )
            utils.insert_keyframe(obj, "rotation_euler", frame, rot)
            # Scale keyframe
            utils.insert_keyframe(obj, "scale", frame, scale)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "rotation_euler":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
                elif fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'BACK'
                        keyframe.easing = 'EASE_OUT'
    
    def apply_bounce_in(self, obj, start_frame, end_frame):
        orig_loc = obj.location.copy()
        duration = end_frame - start_frame
        
        # Define bounce heights and relative timings
        bounce_keyframes = [
            (0.0, -5.0, (0.9, 0.9, 1.3)),    # Start: stretched
            (0.3, 0.0, (1.2, 1.2, 0.8)),     # First impact: squashed
            (0.5, 2.0, (0.9, 0.9, 1.2)),     # First bounce peak: stretched
            (0.7, 0.0, (1.1, 1.1, 0.9)),     # Second impact: less squashed
            (0.85, 0.8, (0.95, 0.95, 1.1)),  # Small bounce
            (1.0, 0.0, (1.0, 1.0, 1.0))      # Final rest position
        ]
        
        # Apply keyframes with relative timing
        for time_pct, height, scale in bounce_keyframes:
            frame = start_frame + int(duration * time_pct)
            # Position keyframe
            pos = (orig_loc.x, orig_loc.y, orig_loc.z + height)
            utils.insert_keyframe(obj, "location", frame, pos)
            # Scale keyframe for squash and stretch
            utils.insert_keyframe(obj, "scale", frame, scale)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "location":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'BOUNCE'
                        keyframe.easing = 'EASE_OUT'
                elif fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
    
    def apply_slide_from_side(self, obj, start_frame, end_frame):
        duration = end_frame - start_frame
        final_pos = obj.location.copy()
        start_rot = obj.rotation_euler.copy()
        
        # Define keyframes with relative timing for position, rotation, and scale
        keyframes = [
            (0.0, -3.0, -15, (0.8, 0.8, 0.8)),     # Start: offset left, tilted, small
            (0.3, -2.0, -10, (0.9, 0.9, 1.1)),     # Moving right, starting to straighten
            (0.6, -0.5, -5, (1.1, 1.1, 0.9)),      # Almost there, slight tilt
            (0.8, 0.2, 2, (1.05, 1.05, 1.05)),     # Overshoot position
            (0.9, 0.1, 1, (0.95, 0.95, 0.95)),     # Settling back
            (1.0, 0.0, 0, (1.0, 1.0, 1.0))         # Final position
        ]
        
        # Apply keyframes with relative timing
        for time_pct, x_offset, rot_z, scale in keyframes:
            frame = start_frame + int(duration * time_pct)
            
            # Position keyframe
            pos = (final_pos.x + x_offset, final_pos.y, final_pos.z)
            utils.insert_keyframe(obj, "location", frame, pos)
            
            # Rotation keyframe
            rot = (
                start_rot[0],
                start_rot[1],
                start_rot[2] + math.radians(rot_z)
            )
            utils.insert_keyframe(obj, "rotation_euler", frame, rot)
            
            # Scale keyframe for subtle squash and stretch
            utils.insert_keyframe(obj, "scale", frame, scale)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "location":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'BACK'
                        keyframe.easing = 'EASE_OUT'
                elif fcurve.data_path == "rotation_euler":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
                elif fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
    
    def apply_fall_from_sky(self, obj, start_frame, end_frame):
        final_pos = obj.location.copy()
        duration = end_frame - start_frame
        
        # Define fall and bounce keyframes with relative timing
        fall_keyframes = [
            (0.0, 10.0, (0.8, 0.8, 1.4)),     # Start high up, stretched
            (0.3, -0.2, (1.4, 1.4, 0.6)),     # First impact, heavily squashed
            (0.5, 2.0, (0.9, 0.9, 1.2)),      # First bounce peak
            (0.7, -0.1, (1.2, 1.2, 0.8)),     # Second impact
            (0.85, 0.5, (0.95, 0.95, 1.1)),   # Small bounce
            (0.92, 0.0, (1.1, 1.1, 0.9)),     # Final small impact
            (1.0, 0.0, (1.0, 1.0, 1.0))       # Rest position
        ]
        
        # Apply keyframes with relative timing
        for time_pct, height, scale in fall_keyframes:
            frame = start_frame + int(duration * time_pct)
            # Position keyframe
            pos = (final_pos.x, final_pos.y, final_pos.z + height)
            utils.insert_keyframe(obj, "location", frame, pos)
            # Scale keyframe for squash and stretch
            utils.insert_keyframe(obj, "scale", frame, scale)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "location":
                    for keyframe in fcurve.keyframe_points:
                        if keyframe.co[0] < start_frame + (duration * 0.3):
                            # Fast fall with ease in
                            keyframe.interpolation = 'SINE'
                            keyframe.easing = 'EASE_IN'
                        else:
                            # Bouncy landing
                            keyframe.interpolation = 'BOUNCE'
                            keyframe.easing = 'EASE_OUT'
                elif fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
    
    def apply_flip_reveal(self, obj, start_frame, end_frame):
        duration = end_frame - start_frame
        start_rot = obj.rotation_euler.copy()
        
        # Define keyframes with relative timing for rotation, scale, and position
        keyframes = [
            (0.0, 0, (0.0, 0.0, 0.0), 0.0),      # Start: invisible
            (0.2, 45, (0.6, 0.6, 0.6), 0.2),     # Starting to appear and flip
            (0.5, 135, (1.2, 1.2, 1.2), -0.1),   # Mid-flip, overshoot scale
            (0.7, 160, (0.9, 0.9, 0.9), 0.05),   # Nearly complete
            (0.85, 175, (1.1, 1.1, 1.1), -0.02), # Final approach
            (1.0, 180, (1.0, 1.0, 1.0), 0.0)     # Final position
        ]
        
        # Store original position
        orig_pos = obj.location.copy()
        
        # Apply keyframes with relative timing
        for time_pct, angle, scale, y_offset in keyframes:
            frame = start_frame + int(duration * time_pct)
            
            # Rotation keyframe (flip around X axis)
            rot = (
                start_rot[0] + math.radians(angle),
                start_rot[1],
                start_rot[2]
            )
            utils.insert_keyframe(obj, "rotation_euler", frame, rot)
            
            # Scale keyframe
            utils.insert_keyframe(obj, "scale", frame, scale)
            
            # Position keyframe (slight Y movement for depth)
            pos = (orig_pos.x, orig_pos.y + y_offset, orig_pos.z)
            utils.insert_keyframe(obj, "location", frame, pos)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "rotation_euler":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
                elif fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_OUT'
                elif fcurve.data_path == "location":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
    
    def apply_typewriter(self, context, obj, start_frame, end_frame):
        if obj.type == 'MESH':
            duration = end_frame - start_frame
            
            # Store original state
            original_hide = obj.hide_viewport
            original_loc = obj.location.copy()
            obj.hide_viewport = True
            
            # Create copy for animation
            copy = obj.copy()
            copy.data = obj.data.copy()
            context.scene.collection.objects.link(copy)
            
            # Define keyframes with relative timing
            keyframes = [
                (0.0, (0.0, 0.0, 0.0), -0.5, 10),    # Start: invisible, offset left, rotated
                (0.2, (0.7, 0.7, 0.7), -0.3, 5),     # Appearing, moving right
                (0.5, (1.1, 1.1, 1.1), -0.1, -3),    # Overshoot
                (0.7, (0.9, 0.9, 0.9), 0.0, 2),      # Settling
                (1.0, (1.0, 1.0, 1.0), 0.0, 0)       # Final position
            ]
            
            # Apply keyframes with relative timing
            for time_pct, scale, x_offset, rot_z in keyframes:
                frame = start_frame + int(duration * time_pct)
                
                # Scale keyframe
                utils.insert_keyframe(copy, "scale", frame, scale)
                
                # Position keyframe
                pos = (original_loc.x + x_offset, original_loc.y, original_loc.z)
                utils.insert_keyframe(copy, "location", frame, pos)
                
                # Rotation keyframe
                rot = copy.rotation_euler.copy()
                rot.z = math.radians(rot_z)
                utils.insert_keyframe(copy, "rotation_euler", frame, rot)
            
            # Set interpolation
            if copy.animation_data and copy.animation_data.action:
                for fcurve in copy.animation_data.action.fcurves:
                    if fcurve.data_path == "scale":
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'SINE'
                            keyframe.easing = 'EASE_OUT'
                    elif fcurve.data_path == "location":
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'BACK'
                            keyframe.easing = 'EASE_OUT'
                    elif fcurve.data_path == "rotation_euler":
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'SINE'
                            keyframe.easing = 'EASE_IN_OUT'
            
            # Schedule cleanup
            def cleanup():
                obj.hide_viewport = original_hide
                if copy:
                    bpy.data.objects.remove(copy, do_unlink=True)
                return None
            
            bpy.app.timers.register(cleanup, first_interval=max(0.1, duration / context.scene.render.fps))
    
    def apply_pulse(self, obj, start_frame, end_frame):
        duration = end_frame - start_frame
        
        # Define keyframes with relative timing for scale and subtle rotation
        keyframes = [
            (0.0, (1.0, 1.0, 1.0), (0, 0, 0)),       # Start: normal size
            (0.2, (1.3, 1.3, 0.8), (0, 0, 2)),       # Quick expand horizontally, compress vertically
            (0.4, (0.8, 0.8, 1.3), (0, 0, -2)),      # Contract horizontally, expand vertically
            (0.6, (1.2, 1.2, 0.9), (0, 0, 1)),       # Second pulse, smaller
            (0.8, (0.9, 0.9, 1.1), (0, 0, -1)),      # Final contraction
            (1.0, (1.0, 1.0, 1.0), (0, 0, 0))        # Return to normal
        ]
        
        # Store original rotation
        orig_rot = obj.rotation_euler.copy()
        
        # Apply keyframes with relative timing
        for time_pct, scale, rot_offset in keyframes:
            frame = start_frame + int(duration * time_pct)
            
            # Scale keyframe
            utils.insert_keyframe(obj, "scale", frame, scale)
            
            # Rotation keyframe (add offset to original rotation)
            rot = (
                orig_rot[0],
                orig_rot[1],
                orig_rot[2] + math.radians(rot_offset[2])
            )
            utils.insert_keyframe(obj, "rotation_euler", frame, rot)
        
        # Set interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path == "scale":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
                elif fcurve.data_path == "rotation_euler":
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = 'SINE'
                        keyframe.easing = 'EASE_IN_OUT'
    
    def apply_elastic(self, obj, start_frame, end_frame):
        duration = end_frame - start_frame
        
        # Define elastic animation with relative timings and overshoot values
        timings = [
            (0.0, (0.0, 0.0, 0.0)),     # Start
            (0.2, (1.5, 1.5, 1.5)),     # First overshoot
            (0.4, (0.7, 0.7, 0.7)),     # First undershoot
            (0.6, (1.2, 1.2, 1.2)),     # Second overshoot
            (0.8, (0.9, 0.9, 0.9)),     # Second undershoot
            (0.9, (1.05, 1.05, 1.05)),  # Final small overshoot
            (1.0, (1.0, 1.0, 1.0))      # Settle
        ]
        
        # Insert keyframes with relative timing
        for time_pct, scale in timings:
            frame = start_frame + int(duration * time_pct)
            utils.insert_keyframe(obj, "scale", frame, scale)
        
        # Set elastic interpolation
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'ELASTIC'
                    keyframe.easing = 'EASE_OUT'
                    # Adjust elastic parameters for smoother motion
                    keyframe.handle_left_type = 'AUTO_CLAMPED'
                    keyframe.handle_right_type = 'AUTO_CLAMPED'
    
    def apply_stagger(self, context, obj, start_frame, end_frame):
        if obj.type == 'MESH':
            duration = end_frame - start_frame
            copies = []
            
            # Define base keyframes for a single element
            base_keyframes = [
                (0.0, (0.0, 0.0, 0.0), -0.3, 10),    # Start: invisible, offset, rotated
                (0.3, (1.2, 1.2, 0.8), -0.1, -5),    # Appear with overshoot
                (0.5, (0.9, 0.9, 1.1), 0.0, 2),      # Undershoot
                (0.7, (1.1, 1.1, 0.9), 0.0, -1),     # Second overshoot
                (1.0, (1.0, 1.0, 1.0), 0.0, 0)       # Final state
            ]
            
            # Create and animate copies with staggered timing
            num_copies = 3
            for i in range(num_copies):
                copy = obj.copy()
                copy.data = obj.data.copy()
                context.scene.collection.objects.link(copy)
                copies.append(copy)
                
                # Calculate delay for this copy
                delay_pct = 0.2 * i  # 20% delay between each copy
                
                # Apply keyframes with staggered timing
                for time_pct, scale, x_offset, rot_z in base_keyframes:
                    # Adjust timing for this copy
                    adjusted_time = time_pct + delay_pct
                    if adjusted_time <= 1.0:  # Only add keyframe if within duration
                        frame = start_frame + int(duration * adjusted_time)
                        
                        # Scale keyframe
                        utils.insert_keyframe(copy, "scale", frame, scale)
                        
                        # Position keyframe (offset horizontally)
                        pos = (obj.location.x + x_offset, obj.location.y, obj.location.z)
                        utils.insert_keyframe(copy, "location", frame, pos)
                        
                        # Rotation keyframe
                        rot = copy.rotation_euler.copy()
                        rot.z = math.radians(rot_z)
                        utils.insert_keyframe(copy, "rotation_euler", frame, rot)
                
                # Set interpolation for this copy
                if copy.animation_data and copy.animation_data.action:
                    for fcurve in copy.animation_data.action.fcurves:
                        if fcurve.data_path == "scale":
                            for keyframe in fcurve.keyframe_points:
                                keyframe.interpolation = 'ELASTIC'
                                keyframe.easing = 'EASE_OUT'
                        elif fcurve.data_path == "location":
                            for keyframe in fcurve.keyframe_points:
                                keyframe.interpolation = 'SINE'
                                keyframe.easing = 'EASE_OUT'
                        elif fcurve.data_path == "rotation_euler":
                            for keyframe in fcurve.keyframe_points:
                                keyframe.interpolation = 'SINE'
                                keyframe.easing = 'EASE_IN_OUT'
            
            # Schedule cleanup
            def cleanup_all():
                for copy in copies:
                    if copy:
                        bpy.data.objects.remove(copy, do_unlink=True)
                return None
            
            bpy.app.timers.register(cleanup_all, first_interval=max(0.1, duration / context.scene.render.fps))

# Main animation presets panel
class ANIM_PT_presets_panel(Panel):
    bl_label = "Animation Presets"
    bl_idname = "ANIM_PT_presets_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def draw(self, context):
        layout = self.layout
        props = context.scene.animation_preset_props

        # Animation Controls Box
        ctrl_box = layout.box()
        ctrl_box.label(text="Animation Controls", icon='SETTINGS')
        
        # Start Frame and Speed in same box
        ctrl_box.prop(props, "start_frame", text="Start Frame")
        
        # Blue highlighted speed slider
        speed_row = ctrl_box.row()
        speed_row.prop(props, "animation_speed", text="Speed")
        speed_row.operator("anim.play_animation", text="", icon='PLAY' if not props.is_playing else 'PAUSE')
        
        # Control buttons in a row
        btn_row = ctrl_box.row(align=True)
        btn_row.scale_y = 1.2
        btn_row.operator("screen.frame_jump", text="", icon='REW').end = False
        btn_row.operator("screen.keyframe_jump", text="", icon='PREV_KEYFRAME').next = False
        btn_row.operator("screen.keyframe_jump", text="", icon='NEXT_KEYFRAME').next = True
        btn_row.operator("screen.frame_jump", text="", icon='FF').end = True
        btn_row.operator("anim.reset_animation", text="", icon='LOOP_BACK')
        
        # Easing in the same box
        ctrl_box.prop(props, "animation_easing", text="Easing")

        # Presets Box
        box = layout.box()
        box.label(text="Animation Presets", icon='ANIM')
        
        # Add optimize button at the top of presets box
        optimize_row = box.row()
        optimize_row.scale_y = 1.2
        optimize_row.operator("anim.optimize_previews", text="Optimize Preview Videos", icon='FILE_MOVIE')
        
        row = box.row(align=True)

        col_left = row.column(align=True)
        col_left.scale_y = 6.0
        col_left.operator("anim.prev_preset", text="", icon='TRIA_LEFT')

        col_center = row.column(align=True)
        col_center.template_icon_view(props, "preset_enum", show_labels=True, scale=6)

        col_right = row.column(align=True)
        col_right.scale_y = 6.0
        col_right.operator("anim.next_preset", text="", icon='TRIA_RIGHT')

        # Preview Video and Apply buttons in a row
        row = box.row(align=True)
        row.scale_y = 1.5
        
        # Video Preview Button
        preview_op = row.operator("anim.play_preview_video", text="Video Preview", icon='FILE_MOVIE')
        preview_op.preset_name = props.preset_enum.replace('PRESET_', '')
        
        # Preview and Apply buttons
        row.operator("anim.preview_preset", text="Live Preview", icon='PLAY')
        
        row = box.row()
        row.scale_y = 1.5
        row.operator("anim.add_preset", text="Apply Preset", icon='CHECKMARK')

# Navigation operators
class ANIM_OT_PrevPreset(Operator):
    bl_idname = "anim.prev_preset"
    bl_label = "Previous Preset"
    
    @classmethod
    def poll(cls, context):
        # Only enable if objects are selected
        return bool(context.selected_objects)
    
    def execute(self, context):
        props = context.scene.animation_preset_props
        items = props.bl_rna.properties["preset_enum"].enum_items
        
        # Find current index
        current_index = 0
        for i, item in enumerate(items):
            if item.identifier == props.preset_enum:
                current_index = i
                break
        
        # Set to previous item or wrap around
        prev_index = current_index - 1
        if prev_index < 0:
            prev_index = len(items) - 1
            
        props.preset_enum = items[prev_index].identifier
        return {'FINISHED'}

class ANIM_OT_NextPreset(Operator):
    bl_idname = "anim.next_preset"
    bl_label = "Next Preset"
    
    @classmethod
    def poll(cls, context):
        # Only enable if objects are selected
        return bool(context.selected_objects)
    
    def execute(self, context):
        props = context.scene.animation_preset_props
        items = props.bl_rna.properties["preset_enum"].enum_items
        
        # Find current index
        current_index = 0
        for i, item in enumerate(items):
            if item.identifier == props.preset_enum:
                current_index = i
                break
        
        # Set to next item or wrap around
        next_index = (current_index + 1) % len(items)
        props.preset_enum = items[next_index].identifier
        return {'FINISHED'}

# Add preview operator
class ANIM_OT_PreviewPreset(Operator):
    bl_idname = "anim.preview_preset"
    bl_label = "Preview Animation Preset"
    
    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)
    
    def execute(self, context):
        props = context.scene.animation_preset_props
        preset = props.preset_enum
        
        # Store original state
        original_states = {}
        for obj in context.selected_objects:
            original_states[obj] = {
                'location': obj.location.copy(),
                'rotation': obj.rotation_euler.copy(),
                'scale': obj.scale.copy()
            }
        
        # Apply the preset
        bpy.ops.anim.add_preset()
        
        # Play the animation
        bpy.ops.screen.animation_play()
        
        # Schedule restoration of original state
        bpy.app.timers.register(lambda: self.restore_original_state(original_states))
        
        return {'FINISHED'}
    
    def restore_original_state(self, original_states):
        for obj, state in original_states.items():
            if obj:
                obj.location = state['location']
                obj.rotation_euler = state['rotation']
                obj.scale = state['scale']
        return None

# Add Preview Video Operator
class ANIM_OT_PlayPreviewVideo(Operator):
    bl_idname = "anim.play_preview_video"
    bl_label = "Play Preview Video"
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to preview",
        default=""
    ) # type: ignore
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        props = context.scene.animation_preset_props
        preview_path = props.get_preview_path(self.preset_name)
        
        if not os.path.exists(preview_path):
            self.report({'WARNING'}, f"No preview video found for {self.preset_name}")
            return {'CANCELLED'}
            
        # Create a new window for video preview
        bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        win = context.window_manager.windows[-1]
        area = win.screen.areas[0]
        area.type = 'CLIP_EDITOR'
        
        # Load and play the video
        try:
            clip = bpy.data.movieclips.load(preview_path)
            area.spaces[0].clip = clip
            area.spaces[0].use_clip = True
            bpy.ops.clip.view_all('INVOKE_DEFAULT')
            area.spaces[0].show_gizmo = False
            area.spaces[0].show_backdrop = True
            bpy.ops.screen.animation_play('INVOKE_DEFAULT')
            
            # Schedule cleanup
            def cleanup(window, clip):
                try:
                    bpy.data.movieclips.remove(clip)
                    bpy.context.window_manager.windows.remove(window)
                except:
                    pass
                return None
            
            bpy.app.timers.register(lambda: cleanup(win, clip), first_interval=5.0)
            
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
            
        return {'FINISHED'}

class ANIM_OT_OptimizePreviews(Operator):
    bl_idname = "anim.optimize_previews"
    bl_label = "Optimize Preview Videos"
    
    def execute(self, context):
        from . import utils
        if utils.optimize_all_previews():
            self.report({'INFO'}, "Successfully optimized preview videos")
        else:
            self.report({'ERROR'}, "Failed to optimize preview videos")
        return {'FINISHED'}

# Register
classes = [
    ANIM_PG_AnimationPresetProperties,
    ANIM_OT_play_animation,
    ANIM_OT_reset_animation,
    ANIM_OT_add_preset,
    ANIM_OT_PrevPreset,
    ANIM_OT_NextPreset,
    ANIM_OT_PreviewPreset,
    ANIM_OT_PlayPreviewVideo,
    ANIM_OT_OptimizePreviews,
    ANIM_PT_presets_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.animation_preset_props = PointerProperty(type=ANIM_PG_AnimationPresetProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.animation_preset_props

if __name__ == "__main__":
    register()