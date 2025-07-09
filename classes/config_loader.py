import os
import yaml
import pygame


def load_image(path: str, size=(32, 32)) -> pygame.Surface:
    """Load an image returning a placeholder if it fails."""
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((255, 0, 255, 255))
        return surf

CONFIG_PATH = 'config/ui.yaml'


class Group:
    """Represents a tile or brush group."""

    def __init__(self, key: int, id: str, icon: str, dir: str):
        self.key = int(key)
        self.id = id
        self.icon_path = icon
        self.dir = dir
        self.icon = load_image(icon)
        self.assets: list[pygame.Surface] = []
        self.load_assets()

    def load_assets(self) -> None:
        if not os.path.isdir(self.dir):
            return
        files = sorted(
            f for f in os.listdir(self.dir)
            if any(f.lower().endswith(ext) for ext in ('.txt', '.png', '.jpg', '.jpeg', '.bmp', '.gif'))
        )
        for fn in files:
            path = os.path.join(self.dir, fn)
            img = load_image(path)
            self.assets.append(img)


class Config:
    """Load UI configuration and asset groups from YAML."""

    def __init__(self, path: str = CONFIG_PATH):
        with open(path, 'r') as f:
            self.data = yaml.safe_load(f)
        self.tile_groups = [Group(**g) for g in self.data['groups']['tile_groups']]
        self.brush_groups = [Group(**g) for g in self.data['groups']['brush_groups']]
        self.ui = self.data['ui']
        self.general = self.data['general']
