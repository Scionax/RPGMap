import os
import pygame
from main import Config

def test_load_config():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.display.init()
    pygame.display.set_mode((1,1))
    cfg = Config('config/ui.yaml')
    assert len(cfg.tile_groups) > 0
    assert len(cfg.brush_groups) > 0
