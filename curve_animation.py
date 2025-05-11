"""Curve Animation Add-on for Blender.

This add-on provides a comprehensive system for creating advanced curve-based animations:
- Multiple curve presets for different animation paths
- Support for animating multiple objects with spacing
- Customizable timing, easing, and looping options
- Path following with rotation and scale controls
- Live preview system with automatic cleanup
- Progress tracking and error handling

Usage:
1. Select object(s) to animate
2. Choose a curve preset from the animation panel
3. Adjust timing and transform settings as needed
4. Use Preview to test the animation
5. Click Apply to create the final animation

Location: View3D > Sidebar > Animation

Note: Requires Blender 2.80 or newer
License: GPL
Version: 1.0.0
Author: BlackboxAI
"""

bl_info = {
    "name": "Curve Animation",
    "author": "BlackboxAI",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Animation",
    "description": "Create advanced curve-based animations with multiple objects",
    "warning": "",
    "doc_url": "https://github.com/blackboxai/curve-animation",
    "tracker_url": "https://github.com/blackboxai/curve-animation/issues",
    "category": "Animation",
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/blackboxai/curve-animation/wiki"
}

import bpy
import os
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    FloatProperty,
    FloatVectorProperty,
)
from . import utils

class CURVE_PG_AnimationProperties(PropertyGroup):
    """Property group for curve animation settings.
    
    This class defines all the properties needed for the curve animation system:
    - Curve selection and presets
    - Animation timing and easing
    - Loop settings and behavior
    - Object spacing for multiple objects
    - Transform settings (rotation, scale)
    - Path following options
    """
    curve_enum: EnumProperty(
        name="Curve Animation",
        description="Select a curve animation preset",
        items=[
            ('Curve Twist', "Curve Twist", "Spiral twist motion"),
            ('Curve Twist 02', "Curve Twist 02", "Double spiral twist"),
            ('Curve Twist 03', "Curve Twist 03", "Triple spiral twist"),
            ('Curve Twist 04', "Curve Twist 04", "Quad spiral twist"),
            ('Curve Twist 05', "Curve Twist 05", "Pentagonal spiral"),
            ('Curve Twist 06', "Curve Twist 06", "Hexagonal spiral"),
            ('Curve Twist 07', "Curve Twist 07", "Wave motion"),
            ('Curve Twist 08', "Curve Twist 08", "Figure 8 motion"),
            ('Curve Twist 09', "Curve Twist 09", "Circular motion"),
            ('Curve Twist 10', "Curve Twist 10", "Infinity loop"),
            ('Curve Twist 11', "Curve Twist 11", "Spiral descent"),
            ('NurbsPath Roll', "NurbsPath Roll", "Rolling motion"),
        ],
        default='Curve Twist'
    ) # type: ignore
    
    # Animation timing
    ease_type: EnumProperty(
        name="Easing",
        description="Animation easing type",
        items=[
            ('LINEAR', "Linear", "No easing"),
            ('SINE', "Sinusoidal", "Smooth acceleration and deceleration"),
            ('QUAD', "Quadratic", "Gradual acceleration"),
            ('CUBIC', "Cubic", "More pronounced acceleration"),
            ('QUART', "Quartic", "Strong acceleration"),
            ('ELASTIC', "Elastic", "Bouncy motion"),
            ('BOUNCE', "Bounce", "Bouncing motion"),
        ],
        default='SINE'
    ) # type: ignore
    
    speed_factor: FloatProperty(
        name="Speed",
        description="Animation speed multiplier",
        default=1.0,
        min=0.1,
        max=10.0,
        soft_min=0.1,
        soft_max=5.0,
        step=10,
        precision=2
    ) # type: ignore
    
    # Animation direction and looping
    reverse_direction: BoolProperty(
        name="Reverse Direction",
        description="Reverse the animation direction along the curve",
        default=False
    ) # type: ignore
    
    loop_animation: BoolProperty(
        name="Loop Animation",
        description="Make the animation loop continuously",
        default=False
    ) # type: ignore
    
    loop_type: EnumProperty(
        name="Loop Type",
        description="How the animation should loop",
        items=[
            ('REPEAT', "Repeat", "Restart from beginning when finished"),
            ('PING_PONG', "Ping Pong", "Reverse direction when finished"),
            ('OFFSET', "Offset", "Offset position slightly each loop"),
        ],
        default='REPEAT'
    ) # type: ignore
    
    loop_offset: FloatProperty(
        name="Loop Offset",
        description="Position offset per loop (for Offset loop type)",
        default=0.1,
        min=-1.0,
        max=1.0,
        step=1,
        precision=3
    ) # type: ignore
    
    # Object spacing
    spacing: FloatProperty(
        name="Object Spacing",
        description="Space between multiple objects along the curve",
        default=1.0,
        min=0.0,
        max=10.0
    ) # type: ignore
    
    # Rotation options
    follow_curve: BoolProperty(
        name="Follow Curve",
        description="Rotate object to follow curve direction",
        default=True
    ) # type: ignore
    
    follow_axis: EnumProperty(
        name="Follow Axis",
        description="Axis that points along the curve",
        items=[
            ('FORWARD_X', "X Forward", "Point X axis along curve"),
            ('FORWARD_Y', "Y Forward", "Point Y axis along curve"),
            ('FORWARD_Z', "Z Forward", "Point Z axis along curve"),
            ('TRACK_NEGATIVE_X', "-X Forward", "Point negative X axis along curve"),
            ('TRACK_NEGATIVE_Y', "-Y Forward", "Point negative Y axis along curve"),
            ('TRACK_NEGATIVE_Z', "-Z Forward", "Point negative Z axis along curve"),
        ],
        default='FORWARD_X'
    ) # type: ignore
    
    up_axis: EnumProperty(
        name="Up Axis",
        description="Axis that points upward",
        items=[
            ('UP_X', "X Up", "Use X as up axis"),
            ('UP_Y', "Y Up", "Use Y as up axis"),
            ('UP_Z', "Z Up", "Use Z as up axis"),
        ],
        default='UP_Z'
    ) # type: ignore
    
    additional_rotation: FloatVectorProperty(
        name="Additional Rotation",
        description="Additional rotation applied during animation",
        subtype='EULER',
        default=(0.0, 0.0, 0.0)
    ) # type: ignore
    
    # Scale animation
    scale_animation: BoolProperty(
        name="Animate Scale",
        description="Animate object scale along the curve",
        default=False
    ) # type: ignore
    
    scale_factor: FloatVectorProperty(
        name="Scale Factor",
        description="Maximum scale factor during animation",
        default=(1.0, 1.0, 1.0),
        min=0.1,
        max=10.0
    ) # type: ignore

class CURVE_OT_ApplyCurveAnimation(Operator):
    """Apply curve animation to selected objects.
    
    This operator handles:
    - Loading and setting up curve objects
    - Applying animations with various settings
    - Multiple object animations with spacing
    - Progress tracking and error handling
    - Constraint and modifier management
    """
    bl_idname = "curve.apply_animation"
    bl_label = "Apply Curve Animation"
    bl_description = "Apply the selected curve animation to selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    track_axis: EnumProperty(
        name="Track Axis",
        description="Axis that points along the curve",
        items=[
            ('FORWARD_X', "X", ""),
            ('FORWARD_Y', "Y", ""),
            ('FORWARD_Z', "Z", ""),
            ('TRACK_NEGATIVE_X', "-X", ""),
            ('TRACK_NEGATIVE_Y', "-Y", ""),
            ('TRACK_NEGATIVE_Z', "-Z", ""),
        ],
        default='FORWARD_X'
    ) # type: ignore

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        # Set progress indicator
        context.window_manager.curve_animation_in_progress = True
        context.area.tag_redraw()

        try:
            settings = context.scene.curve_animation_props
            selected_curve_name = settings.curve_enum
            selected_objects = context.selected_objects
            duration = context.scene.animation_duration

            wm = context.window_manager
            wm.progress_begin(0, len(selected_objects))

            # Validate inputs
            if not selected_objects:
                self.report({'ERROR'}, "No objects selected.")
                return {'CANCELLED'}
            
            if duration < 1:
                self.report({'ERROR'}, "Invalid animation duration.")
                return {'CANCELLED'}

            # Calculate total animation duration including loops
            total_duration = duration
            if settings.loop_animation:
                if settings.loop_type == 'PING_PONG':
                    total_duration *= 2
                elif settings.loop_type == 'OFFSET':
                    total_duration *= 4  # Show 4 loops in preview

            # Set scene frame range for preview
            context.scene.frame_start = 1
            context.scene.frame_end = total_duration
            context.scene.frame_current = 1

            # Get assets path
            assets_folder = utils.get_assets_folder()
            if not assets_folder:
                self.report({'ERROR'}, "Assets folder not found.")
                return {'CANCELLED'}

            blend_file_path = os.path.join(assets_folder, "Assets.blend")
            if not os.path.exists(blend_file_path):
                self.report({'ERROR'}, "Assets.blend file not found in assets folder.")
                return {'CANCELLED'}

            # Track success for multiple objects
            success_count = 0
            failed_objects = []

            try:
                # Get or load curve object
                curve_obj = self.get_or_load_curve(context, selected_curve_name, blend_file_path)
                if not curve_obj:
                    self.report({'ERROR'}, "Failed to load or find curve object")
                    return {'CANCELLED'}

                # Setup curve
                self.setup_curve(curve_obj)

                # Calculate spacing offset for multiple objects
                total_objects = len(selected_objects)
                spacing_offset = settings.spacing if total_objects > 1 else 0

                try:
                    # Apply animation to each selected object
                    for i, obj in enumerate(selected_objects):
                        try:
                            # Update progress
                            wm.progress_update(i)
                            context.area.tag_redraw()
                            
                            # Calculate offset based on object index
                            time_offset = (i * spacing_offset) / duration if spacing_offset > 0 else 0
                            
                            # Setup object
                            self.setup_object(obj, curve_obj)
                            
                            # Calculate adjusted duration based on speed factor
                            adjusted_duration = int(duration / settings.speed_factor)
                            
                            # Apply animation with easing
                            if not self.apply_animation(obj, curve_obj, adjusted_duration, time_offset, settings):
                                failed_objects.append(obj.name)
                                continue
                            
                            # Apply additional transformations
                            if settings.follow_curve:
                                if not self.apply_curve_following(obj, curve_obj, settings):
                                    failed_objects.append(obj.name)
                                    continue
                            
                            if any(r != 0 for r in settings.additional_rotation):
                                self.apply_additional_rotation(obj, settings.additional_rotation, adjusted_duration)
                            
                            if settings.scale_animation:
                                self.apply_scale_animation(obj, settings.scale_factor, adjusted_duration, time_offset)
                            
                            success_count += 1
                            
                        except Exception as obj_error:
                            failed_objects.append(obj.name)
                            self.report({'WARNING'}, f"Failed to animate {obj.name}: {str(obj_error)}")

                    # Set curve visibility
                    self.update_curve_visibility(curve_obj, context.scene.show_animation_paths)

                    # Report results
                    if success_count == total_objects:
                        self.report({'INFO'}, f"Successfully applied animation to all {success_count} objects")
                        return {'FINISHED'}
                    elif success_count > 0:
                        self.report({'WARNING'}, 
                            f"Partially successful: Animated {success_count}/{total_objects} objects. "
                            f"Failed objects: {', '.join(failed_objects)}")
                        return {'FINISHED'}
                    else:
                        self.report({'ERROR'}, f"Failed to animate any objects. Check the system console for details.")
                        return {'CANCELLED'}

                finally:
                    # End progress
                    wm.progress_end()

            except Exception as e:
                self.report({'ERROR'}, f"Animation process failed: {str(e)}")
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Initialization failed: {str(e)}")
            return {'CANCELLED'}

        finally:
            # Clear progress indicator
            if hasattr(context.window_manager, "curve_animation_in_progress"):
                del context.window_manager.curve_animation_in_progress
            context.area.tag_redraw()

    def get_or_load_curve(self, context, curve_name, blend_file_path):
        curve_obj = bpy.data.objects.get(curve_name)
        
        if not curve_obj:
            with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
                if curve_name in data_from.objects:
                    data_to.objects.append(curve_name)
                else:
                    self.report({'ERROR'}, f"Curve '{curve_name}' not found in assets.")
                    return None
            curve_obj = bpy.data.objects.get(curve_name)
        
        if not curve_obj or curve_obj.type != 'CURVE':
            self.report({'ERROR'}, "Selected object is not a curve.")
            return None
            
        return curve_obj

    def setup_curve(self, curve_obj):
        # Unhide curve
        curve_obj.hide_set(False)
        curve_obj.hide_viewport = False
        curve_obj.hide_render = False
        curve_obj.hide_select = False

        for collection in curve_obj.users_collection:
            collection.hide_viewport = False
            collection.hide_render = False

        if not curve_obj.data.use_path:
            curve_obj.data.use_path = True
            curve_obj.data.path_duration = 100

        bpy.context.view_layer.update()

    def setup_object(self, obj, curve_obj):
        # Clear existing animations
        obj.constraints.clear()
        obj.modifiers.clear()
        
        # Add subdivision modifier for smooth deformation
        subd = obj.modifiers.new("Subdivision", 'SUBSURF')
        subd.levels = 2
        subd.render_levels = 3
        subd.subdivision_type = 'CATMULL_CLARK'

        # Add curve modifier
        curve_mod = obj.modifiers.new("Curve Modifier", 'CURVE')
        curve_mod.object = curve_obj
        curve_mod.deform_axis = 'POS_X'

        # Reset rotation
        obj.rotation_euler = (0, 0, 0)

    def apply_animation(self, obj, curve_obj, duration, time_offset, settings):
        """Apply animation to object along curve with specified settings"""
        try:
            # Set up constraints and get follow path constraint
            follow = self.setup_constraints(obj, curve_obj, settings)
            if not follow:
                self.report({'ERROR'}, "Failed to create follow path constraint")
                return False

            # Calculate keyframe times with offset
            start_frame = 1 + int(time_offset * duration)
            end_frame = start_frame + duration

            # Set initial and final offset factors based on direction
            start_factor = 1.0 if settings.reverse_direction else 0.0
            end_factor = 0.0 if settings.reverse_direction else 1.0

            # Clear existing animation data
            if obj.animation_data and obj.animation_data.action:
                for fcurve in obj.animation_data.action.fcurves:
                    if fcurve.data_path.endswith('offset_factor'):
                        obj.animation_data.action.fcurves.remove(fcurve)

            # Insert initial keyframe
            obj.keyframe_insert("location", frame=start_frame)
            follow.offset_factor = start_factor
            follow.keyframe_insert('offset_factor', frame=start_frame)

            if settings.loop_animation:
                if settings.loop_type == 'PING_PONG':
                    self._create_ping_pong_animation(follow, start_frame, duration, start_factor, end_factor)
                elif settings.loop_type == 'OFFSET':
                    self._create_offset_animation(follow, start_frame, duration, start_factor, end_factor, settings)
                else:  # REPEAT
                    self._create_repeat_animation(follow, start_frame, end_frame, end_factor)
            else:
                # Standard non-looping animation
                follow.offset_factor = end_factor
                follow.keyframe_insert('offset_factor', frame=end_frame)

            # Apply interpolation
            self.set_keyframe_interpolation(obj, settings.ease_type, 
                'LINEAR' if settings.loop_type == 'OFFSET' else 'SINE')

            return True

        except Exception as e:
            self.report({'ERROR'}, f"Animation failed: {str(e)}")
            return False

    def _create_ping_pong_animation(self, follow, start_frame, duration, start_factor, end_factor):
        """Create ping-pong style animation"""
        mid_frame = start_frame + duration
        end_frame = start_frame + (duration * 2)
        
        follow.offset_factor = end_factor
        follow.keyframe_insert('offset_factor', frame=mid_frame)
        follow.offset_factor = start_factor
        follow.keyframe_insert('offset_factor', frame=end_frame)

    def _create_offset_animation(self, follow, start_frame, duration, start_factor, end_factor, settings):
        """Create offset-based continuous animation"""
        for i in range(1, 4):
            frame = start_frame + (duration * i)
            offset = i * settings.loop_offset
            factor = (start_factor + offset) if settings.reverse_direction else (end_factor + offset)
            factor = min(max(factor, 0.0), 1.0)  # Clamp between 0 and 1
            
            follow.offset_factor = factor
            follow.keyframe_insert('offset_factor', frame=frame)

    def _create_repeat_animation(self, follow, start_frame, end_frame, end_factor):
        """Create repeating animation"""
        follow.offset_factor = end_factor
        follow.keyframe_insert('offset_factor', frame=end_frame)
        
        if follow.id_data.animation_data and follow.id_data.animation_data.action:
            for fcurve in follow.id_data.animation_data.action.fcurves:
                if fcurve.data_path.endswith('offset_factor'):
                    cycles = fcurve.modifiers.new('CYCLES')
                    cycles.mode_before = 'REPEAT'
                    cycles.mode_after = 'REPEAT'

    def set_keyframe_interpolation(self, obj, interpolation_type, default_type='SINE'):
        """Helper method to set keyframe interpolation"""
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.data_path.endswith('offset_factor'):
                    for keyframe in fcurve.keyframe_points:
                        keyframe.interpolation = interpolation_type or default_type
                        keyframe.handle_left_type = 'AUTO_CLAMPED'
                        keyframe.handle_right_type = 'AUTO_CLAMPED'
        
    def cleanup_animation_data(self, obj):
        """Clean up existing animation data and constraints"""
        # Remove existing animation data
        if obj.animation_data:
            if obj.animation_data.action:
                bpy.data.actions.remove(obj.animation_data.action)
            obj.animation_data_clear()
        
        # Remove existing constraints
        for c in obj.constraints:
            if c.type in {'FOLLOW_PATH', 'TRACK_TO'}:
                obj.constraints.remove(c)

    def setup_constraints(self, obj, curve_obj, settings):
        """Set up all necessary constraints for curve following"""
        try:
            # Clean up existing data
            self.cleanup_animation_data(obj)
            
            # Verify curve object
            if not curve_obj or curve_obj.type != 'CURVE':
                self.report({'ERROR'}, "Invalid curve object")
                return None
            
            # Add follow path constraint
            follow = obj.constraints.new('FOLLOW_PATH')
            if not follow:
                self.report({'ERROR'}, "Could not create follow path constraint")
                return None
                
            # Configure follow path constraint
            follow.target = curve_obj
            follow.use_curve_follow = True
            follow.forward_axis = settings.follow_axis
            follow.up_axis = settings.up_axis
            follow.use_fixed_location = True
            follow.show_expanded = False
            
            # Add track to constraint if follow curve is enabled
            if settings.follow_curve:
                track = obj.constraints.new('TRACK_TO')
                if not track:
                    self.report({'WARNING'}, "Could not create track to constraint")
                else:
                    track.target = curve_obj
                    track.track_axis = settings.follow_axis
                    track.up_axis = settings.up_axis
                    track.show_expanded = False
                    
                    # Move track constraint before follow path for proper order
                    while obj.constraints.find(track.name) < obj.constraints.find(follow.name):
                        bpy.ops.constraint.move_down({'constraint': track})
            
            return follow
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to setup constraints: {str(e)}")
            self.cleanup_animation_data(obj)  # Clean up on failure
            return None

    def apply_curve_following(self, obj, curve_obj, settings):
        """Apply curve following constraints"""
        return self.setup_constraints(obj, curve_obj, settings)

    def apply_additional_rotation(self, obj, rotation, duration):
        # Add keyframes for additional rotation
        obj.keyframe_insert('rotation_euler', frame=1)
        obj.rotation_euler = rotation
        obj.keyframe_insert('rotation_euler', frame=duration)

    def apply_scale_animation(self, obj, scale_factor, duration, time_offset):
        start_frame = 1 + int(time_offset * duration)
        mid_frame = start_frame + int(duration * 0.5)
        end_frame = start_frame + duration
        
        # Create scale animation
        obj.scale = (1, 1, 1)
        obj.keyframe_insert('scale', frame=start_frame)
        obj.scale = scale_factor
        obj.keyframe_insert('scale', frame=mid_frame)
        obj.scale = (1, 1, 1)
        obj.keyframe_insert('scale', frame=end_frame)

    def update_curve_visibility(self, curve_obj, show):
        curve_obj.hide_viewport = not show
        curve_obj.hide_render = not show
        for collection in curve_obj.users_collection:
            collection.hide_viewport = not show

            # Set visibility based on toggle
            show = context.scene.show_animation_paths
            curve_obj.hide_viewport = not show
            curve_obj.hide_render = not show
            for collection in curve_obj.users_collection:
                collection.hide_viewport = not show

            self.report({'INFO'}, f"Applied curve: {selected_curve_name}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

class CURVE_OT_PrevCurve(Operator):
    """Switch to the previous curve animation preset."""
    bl_idname = "curve.prev_animation"
    bl_label = "Previous Curve"
    bl_description = "Switch to the previous curve animation in the list"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        props = context.scene.curve_animation_props
        items = props.bl_rna.properties["curve_enum"].enum_items
        current = [i.identifier for i in items].index(props.curve_enum)
        props.curve_enum = items[(current - 1) % len(items)].identifier
        return {'FINISHED'}

class CURVE_OT_NextCurve(Operator):
    """Switch to the next curve animation preset."""
    bl_idname = "curve.next_animation"
    bl_label = "Next Curve"
    bl_description = "Switch to the next curve animation in the list"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        props = context.scene.curve_animation_props
        items = props.bl_rna.properties["curve_enum"].enum_items
        current = [i.identifier for i in items].index(props.curve_enum)
        props.curve_enum = items[(current + 1) % len(items)].identifier
        return {'FINISHED'}

class CURVE_PT_animation_panel(Panel):
    """Curve Animation Panel
    
    Main interface panel for the curve animation system. Provides:
    - Curve preset selection with preview
    - Animation timing and easing controls
    - Loop and spacing settings
    - Transform options (rotation, scale)
    - Path visibility toggles
    - Preview and apply buttons
    """
    bl_label = "Curve Animation"
    bl_idname = "CURVE_PT_animation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        layout = self.layout
        if hasattr(context.window_manager, "curve_animation_in_progress"):
            layout.label(text="", icon='SORTTIME')

    def draw(self, context):
        layout = self.layout
        props = context.scene.curve_animation_props

        # Curve Selection Box
        box = layout.box()
        box.label(text="Curve Animation Presets", icon='CURVE_DATA')
        
        # Curve Selection Row
        row = box.row(align=True)
        col_left = row.column(align=True)
        col_left.scale_y = 6.0
        col_left.operator("curve.prev_animation", text="", icon='TRIA_LEFT')

        col_center = row.column(align=True)
        col_center.template_icon_view(props, "curve_enum", show_labels=True, scale=6)

        col_right = row.column(align=True)
        col_right.scale_y = 6.0
        col_right.operator("curve.next_animation", text="", icon='TRIA_RIGHT')

        # Animation Timing Box
        timing_box = layout.box()
        timing_box.label(text="Animation Settings", icon='TIME')
        
        # Animation Controls
        timing_col = timing_box.column(align=True)
        
        # Duration and Speed
        row = timing_col.row(align=True)
        row.prop(context.scene, "animation_duration", text="Duration")
        row.prop(props, "speed_factor", text="Speed")
        
        # Easing and Direction
        row = timing_col.row(align=True)
        row.prop(props, "ease_type", text="Easing")
        row.prop(props, "reverse_direction", text="Reverse", toggle=True)
        
        # Loop Settings
        loop_box = timing_box.box()
        loop_box.prop(props, "loop_animation", text="Loop Animation")
        
        # Show loop options only if looping is enabled
        if props.loop_animation:
            loop_col = loop_box.column(align=True)
            loop_col.prop(props, "loop_type", text="Type")
            
            # Show offset control only for OFFSET loop type
            if props.loop_type == 'OFFSET':
                loop_col.prop(props, "loop_offset", text="Offset")
        
        # Multiple Object Settings
        multi_box = layout.box()
        multi_box.label(text="Multiple Objects", icon='OUTLINER_OB_GROUP_INSTANCE')
        multi_box.prop(props, "spacing", text="Object Spacing")

        # Transform Settings Box
        transform_box = layout.box()
        transform_box.label(text="Transform Settings", icon='TRANSFORM')
        
        # Rotation Settings
        rot_col = transform_box.column(align=True)
        rot_col.prop(props, "follow_curve", text="Follow Curve Path")
        
        # Axis controls (only enabled if follow_curve is True)
        axis_box = rot_col.box()
        axis_box.enabled = props.follow_curve
        axis_box.label(text="Follow Path Orientation")
        axis_box.prop(props, "follow_axis", text="Forward")
        axis_box.prop(props, "up_axis", text="Up")
        
        rot_col.prop(props, "additional_rotation", text="Additional Rotation")
        
        # Scale Settings
        scale_col = transform_box.column(align=True)
        scale_col.prop(props, "scale_animation", text="Animate Scale")
        if props.scale_animation:
            scale_col.prop(props, "scale_factor", text="Scale Factor")

        # Preview and Apply Box
        preview_box = layout.box()
        preview_box.label(text="Preview & Apply", icon='PLAY')
        
        # Preview Row
        row = preview_box.row(align=True)
        row.scale_y = 1.5
        row.operator("curve.preview_animation", text="Preview", icon='PLAY')
        row.operator("curve.apply_animation", text="Apply", icon='CHECKMARK')

        # Path Visibility
        vis_box = layout.box()
        vis_box.label(text="Path Options", icon='CURVE_PATH')
        
        # Check if curve exists
        curve_name = props.curve_enum
        curve_exists = bool(bpy.data.objects.get(curve_name))
        
        row = vis_box.row()
        row.enabled = curve_exists
        row.prop(context.scene, "show_animation_paths", text="Show Path")
        if not curve_exists:
            row.label(text="No curve selected/applied", icon='INFO')

# Toggle curve visibility update
def update_path_visibility(self, context):
    show = context.scene.show_animation_paths
    settings = context.scene.curve_animation_props
    curve_name = settings.curve_enum
    
    # Only toggle visibility for the selected/applied curve
    curve_obj = bpy.data.objects.get(curve_name)
    if curve_obj and curve_obj.type == 'CURVE':
        curve_obj.hide_viewport = not show
        curve_obj.hide_render = not show
        for collection in curve_obj.users_collection:
            collection.hide_viewport = not show

class CURVE_OT_PreviewAnimation(Operator):
    """Preview the curve animation on a temporary object.
    
    This operator:
    - Creates a temporary preview object
    - Applies the selected curve animation
    - Plays the animation in the viewport
    - Automatically cleans up after playback
    """
    bl_idname = "curve.preview_animation"
    bl_label = "Preview Curve Animation"
    bl_description = "Create a temporary preview of the selected curve animation"
    bl_options = {'REGISTER', 'INTERNAL'}
    
    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)
    
    def execute(self, context):
        settings = context.scene.curve_animation_props
        selected_curve_name = settings.curve_enum
        selected_objects = context.selected_objects
        
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'CANCELLED'}
            
        # Create a temporary preview object
        preview_obj = bpy.data.objects.new("Preview_Object", None)
        context.scene.collection.objects.link(preview_obj)
        
        # Apply the curve animation to the preview object
        preview_obj.select_set(True)
        bpy.ops.curve.apply_animation()
        
        # Play the animation
        bpy.ops.screen.animation_play()
        
        # Schedule removal of preview object after animation
        bpy.app.timers.register(lambda: self.cleanup_preview(preview_obj))
        
        return {'FINISHED'}
    
    def cleanup_preview(self, preview_obj):
        """Clean up the temporary preview object and its data.
        
        Args:
            preview_obj: The temporary object to remove
            
        Returns:
            None to unregister the timer
        """
        try:
            if preview_obj and preview_obj.name in bpy.data.objects:
                # Stop animation playback
                if bpy.context.screen.is_animation_playing:
                    bpy.ops.screen.animation_cancel()
                
                # Remove object and its data
                mesh = preview_obj.data
                bpy.data.objects.remove(preview_obj, do_unlink=True)
                if mesh and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        except Exception as e:
            print(f"Error cleaning up preview: {str(e)}")
        finally:
            return None  # Unregister timer

# Define classes to register
classes = [
    CURVE_PG_AnimationProperties,
    CURVE_OT_ApplyCurveAnimation,
    CURVE_OT_PrevCurve,
    CURVE_OT_NextCurve,
    CURVE_OT_PreviewAnimation,
    CURVE_PT_animation_panel
]

def register():
    try:
        # Register classes
        for cls in classes:
            bpy.utils.register_class(cls)

        # Register scene properties
        bpy.types.Scene.curve_animation_props = PointerProperty(type=CURVE_PG_AnimationProperties)
        bpy.types.Scene.animation_duration = IntProperty(
            name="Animation Duration",
            description="Duration of the animation in frames",
            default=30,
            min=10,
            max=300
        )
        bpy.types.Scene.show_animation_paths = BoolProperty(
            name="Show Animation Paths",
            description="Toggle visibility of the selected/applied curve",
            default=False,
            update=update_path_visibility
        )
        
        # Register window manager properties for progress tracking
        bpy.types.WindowManager.curve_animation_in_progress = BoolProperty(
            name="Animation in Progress",
            description="Indicates if a curve animation is currently being processed",
            default=False,
            options={'HIDDEN'}  # Hide from UI, only for internal use
        )
 
def unregister():
    try:
        # Clean up window manager properties first
        if hasattr(bpy.types.WindowManager, "curve_animation_in_progress"):
            del bpy.types.WindowManager.curve_animation_in_progress

        # Clean up scene properties
        if hasattr(bpy.types.Scene, "show_animation_paths"):
            del bpy.types.Scene.show_animation_paths
        if hasattr(bpy.types.Scene, "animation_duration"):
            del bpy.types.Scene.animation_duration
        if hasattr(bpy.types.Scene, "curve_animation_props"):
            del bpy.types.Scene.curve_animation_props

        # Unregister classes in reverse order
        for cls in reversed(classes):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                print(f"Failed to unregister {cls.__name__}")
                
