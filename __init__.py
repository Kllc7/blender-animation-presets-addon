bl_info = {
    "name": "Animation Presets and Curve Animations",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Animation",
    "description": "Animation presets and curve-based animations with video previews",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Animation",
}

import bpy # type: ignore
import sys
import os
import importlib
import subprocess
import pkg_resources

required_packages = {
    'numpy': 'numpy>=1.20.0',
    'moviepy': 'moviepy>=1.0.3',
    'pillow': 'pillow>=8.0.0'
}

def install_pip():
    try:
        subprocess.check_call([sys.executable, "-m", "ensurepip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        return True
    except:
        return False

def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", required_packages[package_name]])
        return True
    except:
        return False

def check_dependencies():
    missing = []
    for pkg in required_packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        # Try to install missing packages automatically
        if not install_pip():
            raise ImportError("Failed to install pip. Please install pip manually.")
        for pkg in missing:
            if not install_package(pkg):
                raise ImportError(f"Failed to install {pkg}. Please install it manually.")
    return True, "All dependencies are satisfied"

# Import modules
from . import animation_presets
from . import curve_animation
from . import utils

# List of modules to register/unregister
modules = [animation_presets, curve_animation, utils]

# Initialize preview collections dictionary
preview_collections = {}

class AnimationAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "Jackimation_addon"

    assets_folder: bpy.props.StringProperty(
        name="Select Assets Folder",
        subtype='DIR_PATH',
        default=""
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "assets_folder")

def register():
    """Register all modules when enabling the add-on."""
    # Check dependencies first
    success, message = check_dependencies()
    if not success:
        raise ImportError(f"Dependency Error: {message}")
    
    # First, register all modules
    for module in modules:
        importlib.reload(module)
        module.register()
    
    # Create preview collection for icons
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    
    # Create icons directory if it doesn't exist
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    # Store preview collection
    preview_collections["main"] = pcoll
    
    # Try to remove redundant panel
    utils.remove_redundant_panel()
    
    # Create previews directory if it doesn't exist
    previews_dir = os.path.join(os.path.dirname(__file__), "previews")
    if not os.path.exists(previews_dir):
        os.makedirs(previews_dir)
    
    bpy.utils.register_class(AnimationAddonPreferences)

def unregister():
    """Unregister all modules when disabling the add-on."""
    # Unregister in reverse order
    for module in reversed(modules):
        module.unregister()
    
    # Clear preview collections
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    bpy.utils.unregister_class(AnimationAddonPreferences)

if __name__ == "__main__":
    register()