import pygame
from pygame import Rect


class AssetUI:
    """Handles drawing of the left asset strip and bottom group bar."""

    def __init__(self, app):
        self.app = app

    def draw(self, surface: pygame.Surface) -> None:
        ui = self.app.config.ui
        bottom_rect = Rect((surface.get_width() - ui['bottom_bar_width']) // 2,
                           surface.get_height() - ui['bottom_bar_height'],
                           ui['bottom_bar_width'], ui['bottom_bar_height'])
        pygame.draw.rect(surface, (30, 30, 30), bottom_rect)
        groups = self.app.get_active_groups()
        slot_w = ui['bottom_bar_width'] // 10
        for i, g in enumerate(groups[:10]):
            icon = pygame.transform.scale(g.icon, (ui['tile_preview_size'], ui['tile_preview_size']))
            x = bottom_rect.x + i * slot_w
            y = bottom_rect.y
            surface.blit(icon, (x, y))
            if i == self.app.selected_group:
                pygame.draw.rect(surface, pygame.Color(ui['highlight_color']),
                                 Rect(x, y, slot_w, ui['bottom_bar_height']), 2)

        strip_rect = Rect(0, self.app.menu_bar_height,
                          ui['left_strip_width'], ui['left_strip_visible_rows'] * ui['tile_preview_size'])
        pygame.draw.rect(surface, (30, 30, 30), strip_rect)
        assets = groups[self.app.selected_group].assets
        for idx in range(ui['left_strip_visible_rows']):
            asset_idx = idx + self.app.asset_scroll
            if asset_idx >= len(assets):
                break
            img = pygame.transform.scale(assets[asset_idx],
                                         (ui['tile_preview_size'], ui['tile_preview_size']))
            surface.blit(img, (0, self.app.menu_bar_height + idx * ui['tile_preview_size']))
            if asset_idx == self.app.selected_asset:
                pygame.draw.rect(surface, pygame.Color(ui['highlight_color']),
                                 Rect(0, self.app.menu_bar_height + idx * ui['tile_preview_size'],
                                      ui['left_strip_width'], ui['tile_preview_size']), 2)

    def cycle_selected_asset(self, delta: int) -> None:
        groups = self.app.get_active_groups()
        assets = groups[self.app.selected_group].assets
        if not assets:
            return
        self.app.selected_asset = (self.app.selected_asset + delta) % len(assets)
        if self.app.selected_asset < self.app.asset_scroll:
            self.app.asset_scroll = self.app.selected_asset
        elif self.app.selected_asset >= self.app.asset_scroll + self.app.config.ui['left_strip_visible_rows']:
            self.app.asset_scroll = self.app.selected_asset - self.app.config.ui['left_strip_visible_rows'] + 1
