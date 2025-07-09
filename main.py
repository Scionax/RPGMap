import os
import json
import pygame
from pygame import Rect
import tkinter as tk

from classes.config_loader import Config, load_image, Group
from classes.layer import Layer
from classes.brush import BrushItem
from classes.menu import FileMenu
from classes.ui import AssetUI
from classes.input_handler import InputHandler


def main():
    tool = MapTool()
    tool.run()


class MapTool:
    def __init__(self):
        self.tk_root = tk.Tk()
        self.tk_root.title('RPG Map Tool')
        self.tk_root.protocol('WM_DELETE_WINDOW', self.exit_program)
        self.embed = tk.Frame(self.tk_root, width=800, height=600)
        self.embed.pack(fill=tk.BOTH, expand=True)
        self.tk_root.geometry('800x600')
        self.tk_root.update()
        os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())

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
        self.brush_items: list[BrushItem] = []
        self.mode = 1
        self.running = True
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('RPG Map Tool')

        self.camera = [0, 0]
        self.show_ui = True
        self.selected_group = 0
        self.asset_scroll = 0
        self.selected_asset = 0
        self.dragging_item: BrushItem | None = None
        self.left_button_down = False
        self.right_button_down = False
        self.unsaved_map = False
        self.unsaved_state = False
        self.font = pygame.font.Font(None, 24)
        self.menu_bar_height = 0

        self.file_menu = FileMenu(self, self.tk_root)
        self.asset_ui = AssetUI(self)
        self.input_handler = InputHandler(self)

        self.drag_offset = (0, 0)
        self.wheel_accum = 0.0

    # ---- Utility methods ----
    def get_active_groups(self):
        return self.config.tile_groups if self.mode < 4 else self.config.brush_groups

    def world_to_screen(self, x, y):
        return int((x - self.camera[0]) * self.zoom), int((y - self.camera[1]) * self.zoom)

    def screen_to_world(self, x, y):
        return x / self.zoom + self.camera[0], y / self.zoom + self.camera[1]

    def clamp_camera(self):
        map_w = self.map_tiles_x * self.grid_size
        map_h = self.map_tiles_y * self.grid_size
        vis_w = self.screen.get_width() / self.zoom
        vis_h = self.screen.get_height() / self.zoom
        max_x = max(-128, map_w - vis_w + 128)
        max_y = max(-128, map_h - vis_h + 128)
        self.camera[0] = max(-128, min(self.camera[0], max_x))
        self.camera[1] = max(-128, min(self.camera[1], max_y))

    def center_window(self, window):
        window.update_idletasks()
        w = window.winfo_width()
        h = window.winfo_height()
        px = self.tk_root.winfo_x()
        py = self.tk_root.winfo_y()
        pw = self.tk_root.winfo_width()
        ph = self.tk_root.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        window.geometry(f"+{x}+{y}")

    # ---- Selection and actions ----
    def left_click(self, pos):
        x, y = self.screen_to_world(*pos)
        if self.mode < 4:
            tile_x = int(x // self.grid_size)
            tile_y = int(y // self.grid_size)
            self.layers[self.mode - 1].paint(tile_x, tile_y, (self.selected_group, self.selected_asset))
            self.unsaved_map = True

    def start_drag(self, pos):
        x, y = self.screen_to_world(*pos)
        for item in reversed(self.brush_items):
            g = self.get_active_groups()[item.group_idx]
            img = g.assets[item.asset_idx]
            rect = Rect(item.x, item.y, img.get_width(), img.get_height())
            if rect.collidepoint(x, y):
                self.dragging_item = item
                self.drag_offset = (x - item.x, y - item.y)
                break

    def right_click(self, pos):
        x, y = self.screen_to_world(*pos)
        if self.mode < 4:
            tile_x = int(x // self.grid_size)
            tile_y = int(y // self.grid_size)
            self.layers[self.mode - 1].erase(tile_x, tile_y)
            self.unsaved_map = True
        else:
            for item in reversed(self.brush_items):
                g = self.get_active_groups()[item.group_idx]
                img = g.assets[item.asset_idx]
                rect = Rect(item.x, item.y, img.get_width(), img.get_height())
                if rect.collidepoint(x, y):
                    self.brush_items.remove(item)
                    self.unsaved_state = True
                    break

    # ---- Save/Load helpers ----
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
        self.unsaved_map = False

    def load_map(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        for i in range(3):
            self.layers[i].grid = data.get(f'layer{i+1}', self.layers[i].grid)
        self.unsaved_map = False

    def save_state(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = [{'group': b.group_idx, 'asset': b.asset_idx, 'x': b.x, 'y': b.y} for b in self.brush_items]
        with open(path, 'w') as f:
            json.dump(data, f)
        self.unsaved_state = False

    def load_state(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
        self.brush_items = [BrushItem(d['group'], d['asset'], d['x'], d['y']) for d in data]
        self.unsaved_state = False

    def reload_config(self):
        self.config = Config()

    def toggle_ui(self):
        self.show_ui = not self.show_ui
        self.file_menu.update_file_menu()

    def set_mode(self, mode_idx: int):
        self.mode = mode_idx

    def clear_map(self):
        self.layers = [Layer(self.map_tiles_x, self.map_tiles_y) for _ in range(3)]
        self.unsaved_map = False

    def clear_state(self):
        self.brush_items = []
        self.unsaved_state = False

    def exit_program(self):
        self.running = False

    # ---- Drawing ----
    def draw(self):
        self.screen.fill((50, 50, 50))
        for layer in self.layers:
            for x in range(self.map_tiles_x):
                for y in range(self.map_tiles_y):
                    val = layer.grid[x][y]
                    if val != -1:
                        g_idx, a_idx = val
                        g = self.config.tile_groups[g_idx]
                        img = g.assets[a_idx]
                        sx, sy = self.world_to_screen(x * self.grid_size, y * self.grid_size)
                        sz = int(self.grid_size * self.zoom)
                        img_s = pygame.transform.scale(img, (sz, sz))
                        self.screen.blit(img_s, (sx, sy))
        for item in self.brush_items:
            g = self.config.brush_groups[item.group_idx]
            img = g.assets[item.asset_idx]
            sx, sy = self.world_to_screen(item.x, item.y)
            szx = int(img.get_width() * self.zoom)
            szy = int(img.get_height() * self.zoom)
            img_s = pygame.transform.scale(img, (szx, szy))
            self.screen.blit(img_s, (sx, sy))

        if self.show_ui:
            self.asset_ui.draw(self.screen)
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.tk_root.update_idletasks()
            self.tk_root.update()
            self.input_handler.handle_events()
            self.draw()
            clock.tick(60)
        self.tk_root.destroy()


if __name__ == '__main__':
    main()
