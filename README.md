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

Use the number keys **1-9** to choose a group, scroll the left strip with the mouse wheel, and draw using the left mouse button. Hold the middle mouse button to pan. Press **Tab** to hide/show the UI. `Ctrl+S` saves to a quick file.

Configuration is stored in `config/ui.yaml` which defines tile and brush groups as folders of text files acting as image placeholders.

Sample images are provided for testing. Saved maps are written to `./maps/quick.json` and saved states to `./map-states/quick.json`.
