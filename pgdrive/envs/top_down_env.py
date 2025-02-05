from pgdrive.envs.pgdrive_env import PGDriveEnv
from pgdrive.envs.pgdrive_env import PGDriveEnv
from pgdrive.obs.top_down_obs import TopDownObservation
from pgdrive.obs.top_down_obs_multi_channel import TopDownMultiChannel
from pgdrive.utils import Config


class TopDownSingleFramePGDriveEnv(PGDriveEnv):
    @classmethod
    def default_config(cls) -> Config:
        config = PGDriveEnv.default_config()
        config["vehicle_config"]["lidar"].update({"num_lasers": 0, "distance": 0})  # Remove lidar
        config.update(
            {
                "frame_skip": 5,
                "frame_stack": 3,
                "post_stack": 5,
                "rgb_clip": True,
                "resolution_size": 84,
                "distance": 30
            }
        )
        return config

    def get_single_observation(self, _=None):
        return TopDownObservation(
            self.config["vehicle_config"], self, self.config["rgb_clip"], max_distance=self.config["distance"]
        )


class TopDownPGDriveEnv(TopDownSingleFramePGDriveEnv):
    def get_single_observation(self, _=None):
        return TopDownMultiChannel(
            self.config["vehicle_config"],
            self,
            self.config["rgb_clip"],
            frame_stack=self.config["frame_stack"],
            post_stack=self.config["post_stack"],
            frame_skip=self.config["frame_skip"],
            resolution=(self.config["resolution_size"], self.config["resolution_size"]),
            max_distance=self.config["distance"]
        )


class TopDownPGDriveEnvV2(PGDriveEnv):
    @classmethod
    def default_config(cls) -> Config:
        config = PGDriveEnv.default_config()
        config["vehicle_config"]["lidar"] = {"num_lasers": 0, "distance": 0}  # Remove lidar
        config.update(
            {
                "frame_skip": 5,
                "frame_stack": 3,
                "post_stack": 5,
                "rgb_clip": True,
                "resolution_size": 84,
                "distance": 30
            }
        )
        return config

    def get_single_observation(self, _=None):
        return TopDownMultiChannel(
            self.config["vehicle_config"],
            self,
            self.config["rgb_clip"],
            frame_stack=self.config["frame_stack"],
            post_stack=self.config["post_stack"],
            frame_skip=self.config["frame_skip"],
            resolution=(self.config["resolution_size"], self.config["resolution_size"]),
            max_distance=self.config["distance"]
        )


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    # Test single RGB frame
    # env = TopDownSingleFramePGDriveEnv(dict(use_render=True, environment_num=1, map="C", traffic_density=1.0))
    # env.reset()
    # for _ in range(20):
    #     o, *_ = env.step([0, 1])
    #     assert env.observation_space.contains(o)
    # for _ in range(200):
    #     o, *_ = env.step([0.01, 1])
    #     env.render()
    #     # plt.imshow(o, cmap="gray")
    #     # plt.show()
    #     # print(o.mean())
    # env.close()

    # Test multi-channel frames
    env = TopDownPGDriveEnvV2(dict(environment_num=1, start_seed=5000, distance=30))
    # env = TopDownPGDriveEnv(dict(environment_num=1, map="XTO", traffic_density=0.1, frame_stack=5))
    # env = TopDownPGDriveEnv(dict(use_render=True, manual_control=True))
    env.reset()
    names = [
        "road_network", "navigation", "past_pos", "traffic t", "traffic t-1", "traffic t-2", "traffic t-3",
        "traffic t-4"
    ]
    for _ in range(60):
        o, *_ = env.step([-0.00, 0.2])
        assert env.observation_space.contains(o)
    for _ in range(10000):
        o, r, d, i = env.step([0.0, 1])
        print("Velocity: ", i["velocity"])

        fig, axes = plt.subplots(1, o.shape[-1], figsize=(15, 3))

        # o = env.observations[env.DEFAULT_AGENT].get_screen_window()
        # import numpy as np
        # import pygame
        # o = pygame.surfarray.array3d(o)
        # o = np.transpose(o, (1, 0, 2))
        # axes[0].imshow(o)

        for o_i in range(o.shape[-1]):
            axes[o_i].imshow(o[..., o_i], cmap="gray", vmin=0, vmax=1)
            axes[o_i].set_title(names[o_i])

        fig.suptitle("Multi-channel Top-down Observation")
        plt.show()
        print(o.mean())
    env.close()
