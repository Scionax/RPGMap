class BrushItem:
    """A placed brush asset on the map."""

    def __init__(self, group_idx: int, asset_idx: int, x: float, y: float):
        self.group_idx = group_idx
        self.asset_idx = asset_idx
        self.x = x
        self.y = y
