import pygame

from pgdrive import PGDriveEnv
from pgdrive.component.map.city_map import CityMap
from pgdrive.engine.engine_utils import initialize_engine, close_engine
from pgdrive.obs.top_down_renderer import draw_top_down_map


def _t(num_blocks):
    default_config = PGDriveEnv.default_config()
    initialize_engine(default_config)
    try:
        map_config = default_config["map_config"]
        map_config.update(dict(type="block_num", config=num_blocks))
        map = CityMap(map_config)
        m = draw_top_down_map(map, return_surface=True)
        pygame.image.save(m, "{}.jpg".format(num_blocks))
    finally:
        close_engine()


def test_build_city():
    _t(num_blocks=1)
    _t(num_blocks=3)
    _t(num_blocks=20)


if __name__ == '__main__':
    test_build_city()
