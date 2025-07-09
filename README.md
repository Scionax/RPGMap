# RPG Map Tool

This is a minimal RPG map editor built with Python and Pygame. It supports multiple layers, tile and brush groups, and quick saving/loading.

## Requirements
- Python 3.12+
- `pygame`
- `PyYAML`

Install dependencies:
```
python3 -m pip install pygame PyYAML
```

## Running
```
python3 main.py
```

Use the number keys **1-9** to choose a group, scroll the left strip with the mouse wheel, and draw using the left mouse button. Hold the middle mouse button to pan. Press **Tab** to hide/show the UI. `Ctrl+S` saves to a quick file. A standard menu bar at the top of the window provides options for saving/loading maps and states, changing modes, and editing preferences.

The vertical panel on the left is referred to as the **asset strip** and the bar at the bottom is the **group bar**. The asset strip lists the individual assets in the currently selected group while the group bar displays up to ten available groups.

Configuration is stored in `config/ui.yaml` which defines tile and brush groups as directories of image files (for example `.png` sprites). Older `.txt` placeholders are still supported but no longer required.
The `mouse_scroll_multiplier` option in this file controls how sensitive the mouse wheel is when cycling assets.

Sample images are provided for testing. Saved maps are written to `./maps/quick.json` and saved states to `./map-states/quick.json`.
