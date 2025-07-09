import os
import json
import yaml
import pygame
from pygame import Rect


def load_image(path, size=(32, 32)):
    """Load an image or return a placeholder surface if loading fails."""
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((255, 0, 255, 255))
        return surf

CONFIG_PATH = 'config/ui.yaml'

class Config:
    def __init__(self, path=CONFIG_PATH):
        with open(path, 'r') as f:
            self.data = yaml.safe_load(f)
        self.tile_groups = [Group(**g) for g in self.data['groups']['tile_groups']]
        self.brush_groups = [Group(**g) for g in self.data['groups']['brush_groups']]
        self.ui = self.data['ui']
        self.general = self.data['general']

class Group:
    def __init__(self, key, id, icon, dir):
        self.key = int(key)
        self.id = id
        self.icon_path = icon
        self.dir = dir
        self.icon = load_image(icon)
        self.assets = []
        self.load_assets()

    def load_assets(self):
        if not os.path.isdir(self.dir):
            return
        files = sorted(
            [f for f in os.listdir(self.dir) if f.lower().endswith('.txt')]
        )
        for fn in files:
            path = os.path.join(self.dir, fn)
            img = load_image(path)
            self.assets.append(img)

class Layer:
    def __init__(self, width, height):
        self.grid = [[-1 for _ in range(height)] for _ in range(width)]

    def paint(self, x, y, tile_idx):
        if 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]):
            self.grid[x][y] = tile_idx

    def erase(self, x, y):
        if 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]):
            self.grid[x][y] = -1

class BrushItem:
    def __init__(self, group_idx, asset_idx, x, y):
        self.group_idx = group_idx
        self.asset_idx = asset_idx
        self.x = x
        self.y = y

class MapTool:
    def __init__(self):
        pygame.init()
        self.config = Config()
        self.zoom_levels = self.config.general['zoom_levels']
        self.zoom = self.zoom_levels[1]
        self.pan_speed = self.config.general['pan_speed']
        map_w, map_h = self.config.general['map_size_pixels']
        self.grid_size = self.config.general['grid_size']
        self.map_tiles_x = map_w // self.grid_size
        self.map_tiles_y = map_h // self.grid_size
        self.layers = [Layer(self.map_tiles_x, self.map_tiles_y) for _ in range(3)]
        self.brush_items = []
        self.mode = 1  # 1=Layer1, 2=Layer2,3=Layer3,4=Play
        self.running = True
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('RPG Map Tool')
        self.camera = [0,0]
        self.show_ui = True
        self.selected_group = 0
        self.asset_scroll = 0
        self.selected_asset = 0
        self.dragging_item = None
        self.left_button_down = False
        self.right_button_down = False
        self.load_group_icons()

    def load_group_icons(self):
        for g in self.config.tile_groups + self.config.brush_groups:
            # icons already loaded in Group constructor
            pass

    def get_active_groups(self):
        return self.config.tile_groups if self.mode < 4 else self.config.brush_groups

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    groups = self.get_active_groups()
                    if idx < len(groups):
                        self.selected_group = idx
                        self.selected_asset = 0
                        self.asset_scroll = 0
                elif event.key == pygame.K_PAGEUP:
                    self.asset_scroll = max(0, self.asset_scroll - 1)
                elif event.key == pygame.K_PAGEDOWN:
                    groups = self.get_active_groups()
                    assets = groups[self.selected_group].assets
                    max_scroll = max(0, len(assets) - self.config.ui['left_strip_visible_rows'])
                    self.asset_scroll = min(max_scroll, self.asset_scroll + 1)
                elif event.key == pygame.K_TAB:
                    self.show_ui = not self.show_ui
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    self.quick_save()
                elif event.key == pygame.K_r:
                    self.reload_config()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.MOUSEWHEEL:
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if event.y > 0:
                        self.zoom = self.zoom_levels[max(0, self.zoom_levels.index(self.zoom)-1)]
                    else:
                        self.zoom = self.zoom_levels[min(len(self.zoom_levels)-1, self.zoom_levels.index(self.zoom)+1)]
                else:
                    if event.y > 0:
                        self.asset_scroll = max(0, self.asset_scroll - 1)
                    else:
                        groups = self.get_active_groups()
                        assets = groups[self.selected_group].assets
                        max_scroll = max(0, len(assets) - self.config.ui['left_strip_visible_rows'])
                        self.asset_scroll = min(max_scroll, self.asset_scroll + 1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.left_button_down = True
                    self.left_click(event.pos)
                elif event.button == 3:
                    self.right_button_down = True
                    self.right_click(event.pos)
                elif event.button == 2:
                    self.dragging = True
                    self.last_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.left_button_down = False
                elif event.button == 3:
                    self.right_button_down = False
                elif event.button == 2:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if getattr(self, 'dragging', False):
                    mx, my = event.pos
                    dx = mx - self.last_mouse[0]
                    dy = my - self.last_mouse[1]
                    self.camera[0] -= dx / self.zoom
                    self.camera[1] -= dy / self.zoom
                    self.last_mouse = event.pos
                if self.left_button_down:
                    self.left_click(event.pos)
                if self.right_button_down:
                    self.right_click(event.pos)

    def world_to_screen(self, x, y):
        return int((x - self.camera[0]) * self.zoom), int((y - self.camera[1]) * self.zoom)

    def screen_to_world(self, x, y):
        return x / self.zoom + self.camera[0], y / self.zoom + self.camera[1]

    def left_click(self, pos):
        x, y = self.screen_to_world(*pos)
        if self.mode < 4:
            tile_x = int(x // self.grid_size)
            tile_y = int(y // self.grid_size)
            groups = self.get_active_groups()
            asset = groups[self.selected_group].assets[self.selected_asset]
            idx = self.selected_asset
            self.layers[self.mode-1].paint(tile_x, tile_y, (self.selected_group, idx))
        else:
            self.brush_items.append(BrushItem(self.selected_group, self.selected_asset, x, y))

    def right_click(self, pos):
        x, y = self.screen_to_world(*pos)
        if self.mode < 4:
            tile_x = int(x // self.grid_size)
            tile_y = int(y // self.grid_size)
            self.layers[self.mode-1].erase(tile_x, tile_y)
        else:
            for item in reversed(self.brush_items):
                g = self.get_active_groups()[item.group_idx]
                img = g.assets[item.asset_idx]
                rect = Rect(item.x, item.y, img.get_width(), img.get_height())
                if rect.collidepoint(x, y):
                    self.brush_items.remove(item)
                    break

    def draw(self):
        self.screen.fill((50,50,50))
        # draw grid layers
        for layer_idx, layer in enumerate(self.layers):
            for x in range(self.map_tiles_x):
                for y in range(self.map_tiles_y):
                    val = layer.grid[x][y]
                    if val != -1:
                        g_idx, a_idx = val
                        g = self.config.tile_groups[g_idx]
                        img = g.assets[a_idx]
                        sx, sy = self.world_to_screen(x*self.grid_size, y*self.grid_size)
                        sz = int(self.grid_size * self.zoom)
                        img_s = pygame.transform.scale(img, (sz, sz))
                        self.screen.blit(img_s, (sx, sy))
        # draw brush items
        for item in self.brush_items:
            g = self.config.brush_groups[item.group_idx]
            img = g.assets[item.asset_idx]
            sx, sy = self.world_to_screen(item.x, item.y)
            szx = int(img.get_width()*self.zoom)
            szy = int(img.get_height()*self.zoom)
            img_s = pygame.transform.scale(img, (szx, szy))
            self.screen.blit(img_s, (sx, sy))

        if self.show_ui:
            self.draw_ui()
        pygame.display.flip()

    def draw_ui(self):
        ui = self.config.ui
        bottom_rect = Rect((self.screen.get_width()-ui['bottom_bar_width'])//2,
                           self.screen.get_height()-ui['bottom_bar_height'],
                           ui['bottom_bar_width'], ui['bottom_bar_height'])
        pygame.draw.rect(self.screen, (30,30,30), bottom_rect)
        groups = self.get_active_groups()
        slot_w = ui['bottom_bar_width']//10
        for i,g in enumerate(groups[:10]):
            icon = pygame.transform.scale(g.icon, (ui['tile_preview_size'], ui['tile_preview_size']))
            x = bottom_rect.x + i*slot_w
            y = bottom_rect.y
            self.screen.blit(icon, (x, y))
            if i == self.selected_group:
                pygame.draw.rect(self.screen, pygame.Color(ui['highlight_color']),
                                 Rect(x, y, slot_w, ui['bottom_bar_height']), 2)
        # left strip
        strip_rect = Rect(0,0,ui['left_strip_width'], ui['left_strip_visible_rows']*ui['tile_preview_size'])
        pygame.draw.rect(self.screen, (30,30,30), strip_rect)
        assets = groups[self.selected_group].assets
        for idx in range(ui['left_strip_visible_rows']):
            asset_idx = idx + self.asset_scroll
            if asset_idx >= len(assets):
                break
            img = pygame.transform.scale(assets[asset_idx], (ui['tile_preview_size'], ui['tile_preview_size']))
            self.screen.blit(img, (0, idx*ui['tile_preview_size']))
            if asset_idx == self.selected_asset:
                pygame.draw.rect(self.screen, pygame.Color(ui['highlight_color']),
                                 Rect(0, idx*ui['tile_preview_size'], ui['left_strip_width'], ui['tile_preview_size']), 2)

    def quick_save(self):
        if self.mode < 4:
            self.save_map('maps/quick.json')
        else:
            self.save_state('map-states/quick.json')

    def save_map(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {f'layer{i+1}': layer.grid for i, layer in enumerate(self.layers)}
        with open(path, 'w') as f:
            json.dump(data, f)

    def load_map(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        for i in range(3):
            self.layers[i].grid = data.get(f'layer{i+1}', self.layers[i].grid)

    def save_state(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = [{'group': b.group_idx, 'asset': b.asset_idx, 'x': b.x, 'y': b.y} for b in self.brush_items]
        with open(path, 'w') as f:
            json.dump(data, f)

    def load_state(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        self.brush_items = [BrushItem(d['group'], d['asset'], d['x'], d['y']) for d in data]

    def reload_config(self):
        self.config = Config()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.handle_events()
            self.draw()
            clock.tick(60)

def main():
    tool = MapTool()
    tool.run()

if __name__ == '__main__':
    main()
