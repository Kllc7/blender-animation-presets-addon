# Animation Presets and Curve Animations

A Blender addon that provides animation presets and curve-based animations with video previews.

## Folder Structure

```
YourAddon/
├── __init__.py
├── animation_presets.py
├── curve_animation.py
├── utils.py
├── assets/                # .blend files, curves, etc.
├── previews/              # Video previews (MP4/MOV, square, compressed)
│   └── optimized/         # (optional, for optimized previews)
├── README.txt
```

## Features

- Animation presets with real-time preview
- Curve-based animations
- Video preview system (MP4/MOV, not GIF)
- Real-time speed control
- Animation easing options
- User-selectable asset folder

## Requirements

- Blender 3.0.0 or newer
- Python 3.7 or newer
- Required Python packages (automatically installed):
  - numpy>=1.20.0
  - moviepy>=1.0.3
  - pillow>=8.0.0
  - opencv-python>=4.5.0 (optional)

## Installation

1. Unzip the addon folder (do not install the ZIP directly).
2. In Blender, go to Edit > Preferences > Add-ons > Install, and select the `__init__.py` or the folder.
3. Enable the addon.
4. In the addon preferences, set your Assets Folder (where your .blend files are stored).

## Usage

### Animation Presets

1. Select an object in the 3D viewport
2. Open the Animation tab in the sidebar (N-panel)
3. Choose a preset from the available options
4. Use "Video Preview" to see a recorded preview (MP4/MOV)
5. Use "Live Preview" to see the animation in real-time
6. Click "Apply Preset" to apply the animation to your object

### Curve Animations

1. Select an object in the 3D viewport
2. Open the Animation tab in the sidebar
3. Choose a curve animation
4. Use "Preview" to test the animation
5. Click "Apply Curve Animation" to apply it

### Preview Videos

- Place your preview videos in the `previews/` folder, named exactly as the preset (e.g., `Popup Scale.mp4`).
- Use square, compressed MP4/MOV files for best performance.

### Asset Folder

- Set your asset folder in the addon preferences (see Preferences > Select Assets Folder).
- Store your .blend files and curves in this folder for easy access.

## Troubleshooting

If you encounter dependency issues:
1. Ensure you have internet access and try installing required packages manually
2. Check Blender's system console for error messages

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

from . import utils
assets_folder = utils.get_assets_folder() 

def execute(self, context):
    assets_folder = utils.get_assets_folder()
    if not os.path.exists(assets_folder):
        self.report({'WARNING'}, "Assets folder not found. Please set it in Addon Preferences.")
        return {'CANCELLED'}
    # ... rest of your code ... 
