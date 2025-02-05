import matplotlib.pyplot as plt

from pgdrive import PGDriveEnv
from pgdrive.component.map.city_map import CityMap
from pgdrive.engine.engine_utils import initialize_engine, close_engine, set_global_random_seed
from pgdrive.utils.draw_top_down_map import draw_top_down_map


def _t(num_blocks):
    default_config = PGDriveEnv.default_config()
    initialize_engine(default_config)
    set_global_random_seed(0)
    try:
        map_config = default_config["map_config"]
        map_config.update(dict(type="block_num", config=num_blocks))
        map = CityMap(map_config, random_seed=map_config["seed"])
        fig = draw_top_down_map(map, (1024, 1024))
        plt.imshow(fig, cmap="bone")
        plt.xticks([])
        plt.yticks([])
        plt.title("Building a City with {} blocks!".format(num_blocks))
        plt.show()
    finally:
        close_engine()


if __name__ == "__main__":
    _t(20)
