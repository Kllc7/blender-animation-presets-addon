# To get the user-selected assets folder:
# from . import utils
# assets_folder = utils.get_assets_folder()

import bpy # type: ignore
import os

def insert_keyframe(obj, data_path, frame, value):
    """
    Inserts a keyframe on an object's property.

    :param obj: Blender object to animate
    :param data_path: The property path (e.g., 'location', 'rotation_euler')
    :param frame: The frame number
    :param value: The value to keyframe
    """
    if obj is None:
        return
    
    setattr(obj, data_path, value)  # Set the property
    obj.keyframe_insert(data_path, frame=frame)  # Insert keyframe

def clear_keyframes(obj):
    """
    Clears all keyframes of the given object.

    :param obj: Blender object to clear animation data from
    """
    if obj and obj.animation_data:
        obj.animation_data_clear()

def set_interpolation(obj, interpolation_type="LINEAR"):
    """
    Sets the interpolation type for all keyframes of an object.

    :param obj: Blender object to modify fcurves
    :param interpolation_type: Type of interpolation (e.g., "LINEAR", "BEZIER", "CONSTANT")
    """
    if obj and obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = interpolation_type

def animate_location(obj, start_frame, end_frame, start_pos, end_pos):
    """
    Animates an object's location from start_pos to end_pos between start_frame and end_frame.

    :param obj: Blender object
    :param start_frame: Start frame for animation
    :param end_frame: End frame for animation
    :param start_pos: Starting position (tuple of 3 floats)
    :param end_pos: Ending position (tuple of 3 floats)
    """
    if obj:
        insert_keyframe(obj, "location", start_frame, start_pos)
        insert_keyframe(obj, "location", end_frame, end_pos)

def animate_rotation(obj, start_frame, end_frame, start_rot, end_rot):
    """
    Animates an object's rotation from start_rot to end_rot between start_frame and end_frame.

    :param obj: Blender object
    :param start_frame: Start frame for animation
    :param end_frame: End frame for animation
    :param start_rot: Starting rotation (tuple of 3 floats in radians)
    :param end_rot: Ending rotation (tuple of 3 floats in radians)
    """
    if obj:
        insert_keyframe(obj, "rotation_euler", start_frame, start_rot)
        insert_keyframe(obj, "rotation_euler", end_frame, end_rot)

def animate_scale(obj, start_frame, end_frame, start_scale, end_scale):
    """
    Animates an object's scale from start_scale to end_scale between start_frame and end_frame.

    :param obj: Blender object
    :param start_frame: Start frame for animation
    :param end_frame: End frame for animation
    :param start_scale: Starting scale (tuple of 3 floats)
    :param end_scale: Ending scale (tuple of 3 floats)
    """
    if obj:
        insert_keyframe(obj, "scale", start_frame, start_scale)
        insert_keyframe(obj, "scale", end_frame, end_scale)

# Add this to utils.py
def remove_redundant_panel():
    """Try to remove redundant Animation Controls panel if it exists"""
    for cls in bpy.types.Panel.__subclasses__():
        if hasattr(cls, "bl_idname") and (cls.bl_idname == "ANIMATION_PT_controls" or getattr(cls, "bl_label", "") == "Animation Controls"):
            if hasattr(bpy.types, cls.__name__):
                try:
                    bpy.utils.unregister_class(cls)
                    print(f"Removed redundant panel: {cls.__name__}")
                except:
                    pass

def remove_animation_effects(obj):
    """
    Remove all animation effects (constraints and modifiers) from an object.
    
    :param obj: Blender object to remove animation effects from
    """
    if obj is None:
        return
        
    # Remove constraints related to animation
    animation_constraints = ['FOLLOW_PATH', 'COPY_LOCATION', 'COPY_ROTATION']
    for constraint in list(obj.constraints):  # Create a copy of the list to safely iterate
        if constraint.type in animation_constraints:
            obj.constraints.remove(constraint)
            
    # Remove modifiers related to animation
    animation_modifiers = ['CURVE', 'SUBSURF']
    for modifier in list(obj.modifiers):  # Create a copy of the list to safely iterate
        if modifier.type in animation_modifiers:
            obj.modifiers.remove(modifier)
            
    # Reset visual properties
    if hasattr(obj, "hide_viewport"):
        obj.hide_viewport = False
    if hasattr(obj, "hide_render"):
        obj.hide_render = False

def register():
    """Register function for Blender's add-on system."""
    pass

def unregister():
    """Unregister function for Blender's add-on system."""
    pass

def optimize_preview_video(input_path, output_path, target_size=256):
    """
    Optimize a preview video by:
    1. Resizing to a square format
    2. Compressing with efficient codec
    3. Maintaining aspect ratio with padding
    Uses Pillow instead of OpenCV.
    """
    try:
        import numpy as np
        from PIL import Image
        from moviepy.editor import VideoFileClip
    except ImportError:
        print("Required packages not found. Please install pillow and moviepy.")
        return False

    try:
        # Load the video
        video = VideoFileClip(input_path)
        
        # Calculate new dimensions maintaining aspect ratio
        aspect_ratio = video.w / video.h
        if aspect_ratio > 1:
            # Wider than tall
            new_width = target_size
            new_height = int(target_size / aspect_ratio)
        else:
            # Taller than wide
            new_height = target_size
            new_width = int(target_size * aspect_ratio)
        
        # Create a function to resize and pad the frame using Pillow
        def process_frame(frame):
            # Convert frame (numpy array) to PIL Image
            img = Image.fromarray(frame)
            # Resize maintaining aspect ratio
            img = img.resize((new_width, new_height), Image.LANCZOS)
            # Create square canvas with black padding
            square = Image.new('RGB', (target_size, target_size), (0, 0, 0))
            # Calculate padding
            x_offset = (target_size - new_width) // 2
            y_offset = (target_size - new_height) // 2
            # Paste resized image in center
            square.paste(img, (x_offset, y_offset))
            return np.array(square)
        
        # Process the video
        processed_video = video.fl_image(process_frame)
        
        # Write the optimized video
        processed_video.write_videofile(
            output_path,
            codec='libx264',
            audio=False,
            preset='ultrafast',
            crf=28,  # Higher CRF = more compression
            fps=video.fps
        )
        
        # Clean up
        video.close()
        processed_video.close()
        
        return True
        
    except Exception as e:
        print(f"Error optimizing video: {str(e)}")
        return False

def optimize_all_previews():
    """
    Optimize all preview videos in the previews directory
    """
    addon_dir = os.path.dirname(os.path.dirname(__file__))
    preview_dir = os.path.join(addon_dir, "previews")
    
    if not os.path.exists(preview_dir):
        print("Previews directory not found")
        return False
    
    # Create optimized directory if it doesn't exist
    optimized_dir = os.path.join(preview_dir, "optimized")
    if not os.path.exists(optimized_dir):
        os.makedirs(optimized_dir)
    
    # Process each video file
    for filename in os.listdir(preview_dir):
        if filename.lower().endswith(('.mov', '.mp4', '.avi')):
            input_path = os.path.join(preview_dir, filename)
            output_path = os.path.join(optimized_dir, filename)
            
            print(f"Optimizing {filename}...")
            if optimize_preview_video(input_path, output_path):
                print(f"Successfully optimized {filename}")
            else:
                print(f"Failed to optimize {filename}")
    
    return True

def get_assets_folder():
    import bpy
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    return addon_prefs.assets_folder if addon_prefs.assets_folder else os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')