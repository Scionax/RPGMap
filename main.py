import os
import json
import yaml
import pygame
from pygame import Rect
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox


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
        self.tk_root = tk.Tk()
        self.tk_root.title('RPG Map Tool')
        self.tk_root.geometry('200x1')
        self.tk_root.protocol('WM_DELETE_WINDOW', self.exit_program)
        self.camera = [0,0]
        self.show_ui = True
        self.selected_group = 0
        self.asset_scroll = 0
        self.selected_asset = 0
        self.dragging_item = None
        self.left_button_down = False
        self.right_button_down = False
        self.unsaved_map = False
        self.unsaved_state = False
        self.font = pygame.font.Font(None, 24)
        self.menu_bar_height = 0
        self.init_menu()
        self.load_group_icons()

    def load_group_icons(self):
        for g in self.config.tile_groups + self.config.brush_groups:
            # icons already loaded in Group constructor
            pass

    def init_menu(self):
        menubar = tk.Menu(self.tk_root)

        self.file_menu = tk.Menu(menubar, tearoff=0)
        self.update_file_menu()
        menubar.add_cascade(label='File', menu=self.file_menu)

        mode_menu = tk.Menu(menubar, tearoff=0)
        mode_menu.add_command(label='Layer 1', command=lambda: self.set_mode(1))
        mode_menu.add_command(label='Layer 2', command=lambda: self.set_mode(2))
        mode_menu.add_command(label='Layer 3', command=lambda: self.set_mode(3))
        mode_menu.add_command(label='Play', command=lambda: self.set_mode(4))
        menubar.add_cascade(label='Mode', menu=mode_menu)

        map_menu = tk.Menu(menubar, tearoff=0)
        map_menu.add_command(label='Preferences', command=self.open_preferences_dialog)
        map_menu.add_command(label='Save Map', command=self.open_save_map_dialog)
        map_menu.add_command(label='Load Map', command=self.open_load_map_dialog)
        map_menu.add_command(label='Clear Map', command=self.clear_map_prompt)
        menubar.add_cascade(label='Map', menu=map_menu)

        session_menu = tk.Menu(menubar, tearoff=0)
        session_menu.add_command(label='Save State', command=self.open_save_state_dialog)
        session_menu.add_command(label='Load State', command=self.open_load_state_dialog)
        session_menu.add_command(label='Clear State', command=self.clear_state_prompt)
        menubar.add_cascade(label='Session', menu=session_menu)

        self.tk_root.config(menu=menubar)
        self.menubar = menubar

    def update_file_menu(self):
        self.file_menu.delete(0, tk.END)
        self.file_menu.add_command(label='Hide UI' if self.show_ui else 'Show UI', command=self.toggle_ui)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command=self.exit_program)

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
                    self.clamp_camera()
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
                    self.clamp_camera()
                    self.last_mouse = event.pos
                if self.left_button_down:
                    self.left_click(event.pos)
                if self.right_button_down:
                    self.right_click(event.pos)

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

    def left_click(self, pos):
        x, y = self.screen_to_world(*pos)
        if self.mode < 4:
            tile_x = int(x // self.grid_size)
            tile_y = int(y // self.grid_size)
            groups = self.get_active_groups()
            asset = groups[self.selected_group].assets[self.selected_asset]
            idx = self.selected_asset
            self.layers[self.mode-1].paint(tile_x, tile_y, (self.selected_group, idx))
            self.unsaved_map = True
        else:
            self.brush_items.append(BrushItem(self.selected_group, self.selected_asset, x, y))
            self.unsaved_state = True

    def right_click(self, pos):
        x, y = self.screen_to_world(*pos)
        if self.mode < 4:
            tile_x = int(x // self.grid_size)
            tile_y = int(y // self.grid_size)
            self.layers[self.mode-1].erase(tile_x, tile_y)
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
        strip_rect = Rect(0,self.menu_bar_height,ui['left_strip_width'], ui['left_strip_visible_rows']*ui['tile_preview_size'])
        pygame.draw.rect(self.screen, (30,30,30), strip_rect)
        assets = groups[self.selected_group].assets
        for idx in range(ui['left_strip_visible_rows']):
            asset_idx = idx + self.asset_scroll
            if asset_idx >= len(assets):
                break
            img = pygame.transform.scale(assets[asset_idx], (ui['tile_preview_size'], ui['tile_preview_size']))
            self.screen.blit(img, (0, self.menu_bar_height + idx*ui['tile_preview_size']))
            if asset_idx == self.selected_asset:
                pygame.draw.rect(self.screen, pygame.Color(ui['highlight_color']),
                                 Rect(0, self.menu_bar_height + idx*ui['tile_preview_size'], ui['left_strip_width'], ui['tile_preview_size']), 2)


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
        self.update_file_menu()

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

    # ------------------- Menu callbacks -------------------
    def open_preferences_dialog(self):
        root = tk.Tk()
        root.withdraw()
        try:
            zoom = simpledialog.askfloat('Preferences', 'Zoom:', initialvalue=self.zoom, parent=root)
            if zoom is not None:
                self.zoom = zoom
            pan = simpledialog.askinteger('Preferences', 'Pan speed:', initialvalue=self.pan_speed, parent=root)
            if pan is not None:
                self.pan_speed = pan
            width = simpledialog.askinteger('Preferences', 'Map width:', initialvalue=self.map_tiles_x * self.grid_size, parent=root)
            height = simpledialog.askinteger('Preferences', 'Map height:', initialvalue=self.map_tiles_y * self.grid_size, parent=root)
            if width and height:
                self.map_tiles_x = width // self.grid_size
                self.map_tiles_y = height // self.grid_size
                self.layers = [Layer(self.map_tiles_x, self.map_tiles_y) for _ in range(3)]
                self.camera = [0, 0]
                self.unsaved_map = False
            self.clamp_camera()
        finally:
            root.destroy()

    def open_save_map_dialog(self):
        root = tk.Tk()
        root.withdraw()
        try:
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')], initialdir='maps', initialfile='map.json', parent=root)
            if path:
                self.save_map(path)
        finally:
            root.destroy()

    def open_load_map_dialog(self):
        root = tk.Tk()
        root.withdraw()
        try:
            path = filedialog.askopenfilename(defaultextension='.json', filetypes=[('JSON','*.json')], initialdir='maps', parent=root)
            if path:
                self.load_map(path)
        finally:
            root.destroy()

    def clear_map_prompt(self):
        if self.unsaved_map:
            root = tk.Tk()
            root.withdraw()
            try:
                if messagebox.askyesno('Clear Map?', 'Unsaved changes! Clear anyway?', parent=root):
                    self.clear_map()
            finally:
                root.destroy()
        else:
            self.clear_map()

    def open_save_state_dialog(self):
        root = tk.Tk()
        root.withdraw()
        try:
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')], initialdir='map-states', initialfile='state.json', parent=root)
            if path:
                self.save_state(path)
        finally:
            root.destroy()

    def open_load_state_dialog(self):
        root = tk.Tk()
        root.withdraw()
        try:
            path = filedialog.askopenfilename(defaultextension='.json', filetypes=[('JSON','*.json')], initialdir='map-states', parent=root)
            if path:
                self.load_state(path)
        finally:
            root.destroy()

    def clear_state_prompt(self):
        if self.unsaved_state:
            root = tk.Tk()
            root.withdraw()
            try:
                if messagebox.askyesno('Clear State?', 'Unsaved changes! Clear anyway?', parent=root):
                    self.clear_state()
            finally:
                root.destroy()
        else:
            self.clear_state()

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.tk_root.update_idletasks()
            self.tk_root.update()
            self.handle_events()
            self.draw()
            clock.tick(60)
        self.tk_root.destroy()

def main():
    tool = MapTool()
    tool.run()

if __name__ == '__main__':
    main()
