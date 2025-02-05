from pgdrive.component.map.base_map import BaseMap, MapGenerateMethod
from pgdrive.envs.pgdrive_env import PGDriveEnv
from pgdrive.utils import setup_logger

setup_logger(debug=True)

if __name__ == "__main__":
    import numpy as np

    env = PGDriveEnv(
        {
            "environment_num": 4,
            "traffic_density": 0.0,
            "use_render": True,
            "map_config": {
                BaseMap.GENERATE_TYPE: MapGenerateMethod.BIG_BLOCK_SEQUENCE,
                BaseMap.GENERATE_CONFIG: "SSSSSSSSSSSSS",
            },
            "manual_control": True
        }
    )
    acc = [0, 1]
    brake = [-1, -np.nan]
    env.reset()
    for i in range(1, 100000):
        o, r, d, info = env.step(acc)
        print(
            "new:{}, old:{}, diff:{}".format(
                env.vehicle.speed, env.vehicle.system.get_current_speed_km_hour(),
                env.vehicle.speed - env.vehicle.system.get_current_speed_km_hour()
            )
        )
        env.render("Test: {}".format(i))
    env.close()
