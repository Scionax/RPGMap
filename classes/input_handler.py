import pygame
from pygame import Rect

from .brush import BrushItem


class InputHandler:
    """Handle pygame input events."""

    def __init__(self, app):
        self.app = app

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mousewheel(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mousebuttondown(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self._handle_mousebuttonup(event)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mousemotion(event)

    # ---------------- internal handlers -----------------
    def _handle_keydown(self, event):
        if pygame.K_1 <= event.key <= pygame.K_9:
            idx = event.key - pygame.K_1
            groups = self.app.get_active_groups()
            if idx < len(groups):
                self.app.selected_group = idx
                self.app.selected_asset = 0
                self.app.asset_scroll = 0
        elif event.key == pygame.K_PAGEUP:
            self.app.asset_ui.cycle_selected_asset(-1)
        elif event.key == pygame.K_PAGEDOWN:
            self.app.asset_ui.cycle_selected_asset(1)
        elif event.key == pygame.K_TAB:
            self.app.show_ui = not self.app.show_ui
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.app.quick_save()
        elif event.key == pygame.K_r:
            self.app.reload_config()
        elif event.key == pygame.K_ESCAPE:
            self.app.running = False
        elif event.key == pygame.K_SPACE and self.app.mode == 4:
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.app.screen_to_world(mx, my)
            self.app.brush_items.append(BrushItem(self.app.selected_group, self.app.selected_asset, wx, wy))
            self.app.unsaved_state = True

    def _handle_mousewheel(self, event):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            if event.y > 0:
                self.app.zoom = self.app.zoom_levels[max(0, self.app.zoom_levels.index(self.app.zoom) - 1)]
            else:
                self.app.zoom = self.app.zoom_levels[min(len(self.app.zoom_levels) - 1, self.app.zoom_levels.index(self.app.zoom) + 1)]
            self.app.clamp_camera()
        else:
            self.app.wheel_accum += event.y
            while self.app.wheel_accum >= 1:
                self.app.asset_ui.cycle_selected_asset(-1)
                self.app.wheel_accum -= 1
            while self.app.wheel_accum <= -1:
                self.app.asset_ui.cycle_selected_asset(1)
                self.app.wheel_accum += 1

    def _handle_mousebuttondown(self, event):
        if event.button in (4, 5):
            delta = 1 if event.button == 4 else -1
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                if delta > 0:
                    self.app.zoom = self.app.zoom_levels[max(0, self.app.zoom_levels.index(self.app.zoom) - 1)]
                else:
                    self.app.zoom = self.app.zoom_levels[min(len(self.app.zoom_levels) - 1, self.app.zoom_levels.index(self.app.zoom) + 1)]
                self.app.clamp_camera()
            else:
                self.app.asset_ui.cycle_selected_asset(delta)
        elif event.button == 1:
            self.app.left_button_down = True
            if self.app.mode < 4:
                self.app.left_click(event.pos)
            else:
                self.app.start_drag(event.pos)
        elif event.button == 3:
            self.app.right_button_down = True
            self.app.right_click(event.pos)
        elif event.button == 2:
            self.app.dragging = True
            self.app.last_mouse = event.pos

    def _handle_mousebuttonup(self, event):
        if event.button == 1:
            self.app.left_button_down = False
            if self.app.mode == 4:
                self.app.dragging_item = None
        elif event.button == 3:
            self.app.right_button_down = False
        elif event.button == 2:
            self.app.dragging = False

    def _handle_mousemotion(self, event):
        if getattr(self.app, 'dragging', False):
            mx, my = event.pos
            dx = mx - self.app.last_mouse[0]
            dy = my - self.app.last_mouse[1]
            self.app.camera[0] -= dx / self.app.zoom
            self.app.camera[1] -= dy / self.app.zoom
            self.app.clamp_camera()
            self.app.last_mouse = event.pos
        if self.app.mode == 4 and self.app.left_button_down and self.app.dragging_item:
            mx, my = self.app.screen_to_world(*event.pos)
            self.app.dragging_item.x = mx - self.app.drag_offset[0]
            self.app.dragging_item.y = my - self.app.drag_offset[1]
            self.app.unsaved_state = True
        elif self.app.left_button_down and self.app.mode < 4:
            self.app.left_click(event.pos)
        if self.app.right_button_down:
            self.app.right_click(event.pos)
