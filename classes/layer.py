class Layer:
    """A single tile layer grid."""

    def __init__(self, width: int, height: int):
        self.grid = [[-1 for _ in range(height)] for _ in range(width)]

    def paint(self, x: int, y: int, tile_idx):
        if 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]):
            self.grid[x][y] = tile_idx

    def erase(self, x: int, y: int) -> None:
        if 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]):
            self.grid[x][y] = -1
