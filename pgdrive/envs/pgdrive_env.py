import copy
import logging
import os.path as osp
from typing import Union, Dict, AnyStr, Tuple

import numpy as np
from pgdrive.component.blocks.first_block import FirstPGBlock
from pgdrive.component.map.base_map import BaseMap, MapGenerateMethod, parse_map_config
from pgdrive.component.vehicle.base_vehicle import BaseVehicle
from pgdrive.constants import DEFAULT_AGENT, TerminationState
from pgdrive.engine.engine_utils import engine_initialized
from pgdrive.envs.base_env import BasePGDriveEnv
from pgdrive.manager.traffic_manager import TrafficMode
from pgdrive.obs.image_obs import ImageStateObservation
from pgdrive.obs.state_obs import LidarStateObservation
from pgdrive.utils import clip, Config, concat_step_infos, get_np_random

pregenerated_map_file = osp.join(
    osp.dirname(osp.dirname(osp.abspath(__file__))), "assets", "maps",
    "20210814_generated_maps_start_seed_0_environment_num_30000.json"
)
PGDriveEnv_DEFAULT_CONFIG = dict(
    # ===== Generalization =====
    start_seed=0,
    environment_num=1,

    # ===== Map Config =====
    map=3,  # int or string: an easy way to fill map_config
    random_lane_width=False,
    random_lane_num=False,
    map_config={
        BaseMap.GENERATE_TYPE: MapGenerateMethod.BIG_BLOCK_NUM,
        BaseMap.GENERATE_CONFIG: None,  # it can be a file path / block num / block ID sequence
        BaseMap.LANE_WIDTH: 3.5,
        BaseMap.LANE_NUM: 3,
        "exit_length": 50,
    },
    load_map_from_json=True,  # Whether to load maps from pre-generated file
    _load_map_from_json=pregenerated_map_file,  # The path to the pre-generated file

    # ===== Observation =====
    use_topdown=False,  # Use top-down view
    offscreen_render=False,
    _disable_detector_mask=False,

    # ===== Traffic =====
    traffic_density=0.1,
    traffic_mode=TrafficMode.Trigger,  # "Respawn", "Trigger", "Hybrid"
    random_traffic=False,  # Traffic is randomized at default.

    # ===== Object =====
    accident_prob=0.,  # accident may happen on each block with this probability, except multi-exits block

    # ===== Others =====
    auto_termination=False,  # Whether to done the environment after 250*(num_blocks+1) steps.
    use_saver=False,
    save_level=0.5,

    # ===== Single-agent vehicle config =====
    vehicle_config=dict(
        # ===== vehicle module config =====
        # laser num, distance, other vehicle info num
        lidar=dict(num_lasers=240, distance=50, num_others=4, gaussian_noise=0.0, dropout_prob=0.0),
        side_detector=dict(num_lasers=0, distance=50, gaussian_noise=0.0, dropout_prob=0.0),
        lane_line_detector=dict(num_lasers=0, distance=20, gaussian_noise=0.0, dropout_prob=0.0),
        show_lidar=False,
        mini_map=(84, 84, 250),  # buffer length, width
        rgb_camera=(84, 84),  # buffer length, width
        depth_camera=(84, 84, True),  # buffer length, width, view_ground
        show_side_detector=False,
        show_lane_line_detector=False,

        # ===== use image =====
        image_source="rgb_camera",  # take effect when only when offscreen_render == True

        # ===== vehicle spawn and destination =====
        spawn_lane_index=(FirstPGBlock.NODE_1, FirstPGBlock.NODE_2, 0),
        spawn_longitude=5.0,
        spawn_lateral=0.0,
        destination_node=None,

        # ==== others ====
        overtake_stat=False,  # we usually set to True when evaluation
        action_check=False,
        random_color=False,
    ),
    rgb_clip=True,
    gaussian_noise=0.0,
    dropout_prob=0.0,

    # ===== Reward Scheme =====
    # See: https://github.com/decisionforce/pgdrive/issues/283
    success_reward=10.0,
    out_of_road_penalty=5.0,
    crash_vehicle_penalty=5.0,
    crash_object_penalty=5.0,
    acceleration_penalty=0.0,
    low_speed_penalty=0.0,
    driving_reward=1.0,
    general_penalty=0.0,
    speed_reward=0.1,
    use_lateral=False,

    # ===== Cost Scheme =====
    crash_vehicle_cost=1,
    crash_object_cost=1,
    out_of_road_cost=1.,
    out_of_route_done=False,
)


class PGDriveEnv(BasePGDriveEnv):
    @classmethod
    def default_config(cls) -> "Config":
        config = super(PGDriveEnv, cls).default_config()
        config.update(PGDriveEnv_DEFAULT_CONFIG)
        config.register_type("map", str, int)
        config["map_config"].register_type("config", None)
        return config

    def __init__(self, config: dict = None):
        self.default_config_copy = Config(self.default_config(), unchangeable=True)
        super(PGDriveEnv, self).__init__(config)

    def _merge_extra_config(self, config: Union[dict, "Config"]) -> "Config":
        config = self.default_config().update(config, allow_add_new_key=False)
        if config["vehicle_config"]["lidar"]["distance"] > 50:
            config["max_distance"] = config["vehicle_config"]["lidar"]["distance"]
        return config

    def _post_process_config(self, config):
        config = super(PGDriveEnv, self)._post_process_config(config)
        if not config["rgb_clip"]:
            logging.warning(
                "You have set rgb_clip = False, which means the observation will be uint8 values in [0, 255]. "
                "Please make sure you have parsed them later before feeding them to network!"
            )
        config["map_config"] = parse_map_config(
            easy_map_config=config["map"], new_map_config=config["map_config"], default_config=self.default_config_copy
        )
        config["vehicle_config"]["rgb_clip"] = config["rgb_clip"]
        config["vehicle_config"]["random_agent_model"] = config["random_agent_model"]
        if config.get("gaussian_noise", 0) > 0:
            assert config["vehicle_config"]["lidar"]["gaussian_noise"] == 0, "You already provide config!"
            assert config["vehicle_config"]["side_detector"]["gaussian_noise"] == 0, "You already provide config!"
            assert config["vehicle_config"]["lane_line_detector"]["gaussian_noise"] == 0, "You already provide config!"
            config["vehicle_config"]["lidar"]["gaussian_noise"] = config["gaussian_noise"]
            config["vehicle_config"]["side_detector"]["gaussian_noise"] = config["gaussian_noise"]
            config["vehicle_config"]["lane_line_detector"]["gaussian_noise"] = config["gaussian_noise"]
        if config.get("dropout_prob", 0) > 0:
            assert config["vehicle_config"]["lidar"]["dropout_prob"] == 0, "You already provide config!"
            assert config["vehicle_config"]["side_detector"]["dropout_prob"] == 0, "You already provide config!"
            assert config["vehicle_config"]["lane_line_detector"]["dropout_prob"] == 0, "You already provide config!"
            config["vehicle_config"]["lidar"]["dropout_prob"] = config["dropout_prob"]
            config["vehicle_config"]["side_detector"]["dropout_prob"] = config["dropout_prob"]
            config["vehicle_config"]["lane_line_detector"]["dropout_prob"] = config["dropout_prob"]
        return config

    def _get_observations(self):
        return {DEFAULT_AGENT: self.get_single_observation(self.config["vehicle_config"])}

    def done_function(self, vehicle_id: str):
        vehicle = self.vehicles[vehicle_id]
        done = False
        done_info = dict(
            crash_vehicle=False, crash_object=False, crash_building=False, out_of_road=False, arrive_dest=False
        )
        if vehicle.arrive_destination:
            done = True
            logging.info("Episode ended! Reason: arrive_dest.")
            done_info[TerminationState.SUCCESS] = True
        if self._is_out_of_road(vehicle):
            done = True
            logging.info("Episode ended! Reason: out_of_road.")
            done_info[TerminationState.OUT_OF_ROAD] = True
        if vehicle.crash_vehicle:
            done = True
            logging.info("Episode ended! Reason: crash vehicle ")
            done_info[TerminationState.CRASH_VEHICLE] = True
        if vehicle.crash_object:
            done = True
            done_info[TerminationState.CRASH_OBJECT] = True
            logging.info("Episode ended! Reason: crash object ")
        if vehicle.crash_building:
            done = True
            done_info[TerminationState.CRASH_BUILDING] = True
            logging.info("Episode ended! Reason: crash building ")

        # for compatibility
        # crash almost equals to crashing with vehicles
        done_info[TerminationState.CRASH] = (
            done_info[TerminationState.CRASH_VEHICLE] or done_info[TerminationState.CRASH_OBJECT]
            or done_info[TerminationState.CRASH_BUILDING]
        )
        return done, done_info

    def cost_function(self, vehicle_id: str):
        vehicle = self.vehicles[vehicle_id]
        step_info = dict()
        step_info["cost"] = 0
        if self._is_out_of_road(vehicle):
            step_info["cost"] = self.config["out_of_road_cost"]
        elif vehicle.crash_vehicle:
            step_info["cost"] = self.config["crash_vehicle_cost"]
        elif vehicle.crash_object:
            step_info["cost"] = self.config["crash_object_cost"]
        return step_info['cost'], step_info

    def _is_out_of_road(self, vehicle):
        # A specified function to determine whether this vehicle should be done.
        # return vehicle.on_yellow_continuous_line or (not vehicle.on_lane) or vehicle.crash_sidewalk
        ret = vehicle.on_yellow_continuous_line or vehicle.on_white_continuous_line or \
              (not vehicle.on_lane) or vehicle.crash_sidewalk
        if self.config["out_of_route_done"]:
            ret = ret or vehicle.out_of_route
        return ret

    def reward_function(self, vehicle_id: str):
        """
        Override this func to get a new reward function
        :param vehicle_id: id of BaseVehicle
        :return: reward
        """
        vehicle = self.vehicles[vehicle_id]
        step_info = dict()

        # Reward for moving forward in current lane
        if vehicle.lane in vehicle.navigation.current_ref_lanes:
            current_lane = vehicle.lane
            positive_road = 1
        else:
            current_lane = vehicle.navigation.current_ref_lanes[0]
            current_road = vehicle.current_road
            positive_road = 1 if not current_road.is_negative_road() else -1
        long_last, _ = current_lane.local_coordinates(vehicle.last_position)
        long_now, lateral_now = current_lane.local_coordinates(vehicle.position)

        # reward for lane keeping, without it vehicle can learn to overtake but fail to keep in lane
        if self.config["use_lateral"]:
            lateral_factor = clip(1 - 2 * abs(lateral_now) / vehicle.navigation.get_current_lane_width(), 0.0, 1.0)
        else:
            lateral_factor = 1.0

        reward = 0.0
        reward += self.config["driving_reward"] * (long_now - long_last) * lateral_factor * positive_road
        reward += self.config["speed_reward"] * (vehicle.speed / vehicle.max_speed) * positive_road

        step_info["step_reward"] = reward

        if vehicle.arrive_destination:
            reward = +self.config["success_reward"]
        elif self._is_out_of_road(vehicle):
            reward = -self.config["out_of_road_penalty"]
        elif vehicle.crash_vehicle:
            reward = -self.config["crash_vehicle_penalty"]
        elif vehicle.crash_object:
            reward = -self.config["crash_object_penalty"]
        return reward, step_info

    def dump_all_maps(self):
        assert not engine_initialized(), \
            "We assume you generate map files in independent tasks (not in training). " \
            "So you should run the generating script without calling reset of the " \
            "environment."

        self.lazy_init()  # it only works the first time when reset() is called to avoid the error when render
        assert engine_initialized()

        for seed in range(self.start_seed, self.start_seed + self.env_num):
            all_config = self.config.copy()
            all_config["map_config"]["seed"] = seed
            # map_config = copy.deepcopy(self.config["map_config"])
            # map_config.update({"seed": seed})
            # set_global_random_seed(seed)

            self.engine.map_manager.update_map(all_config, current_seed=seed)
            # new_map = self.engine.map_manager.spawn_object(PGMap, map_config=map_config, random_seed=None)
            # self.pg_maps[current_seed] = new_map
            # self.engine.map_manager.unload_map(new_map)
            print("Finish generating map with seed: {}".format(seed))

        map_data = dict()
        for seed, map in self.maps.items():
            assert map is not None
            map_data[seed] = map.save_map()

        return_data = dict(map_config=self.config["map_config"].copy().get_dict(), map_data=copy.deepcopy(map_data))
        return return_data

    def toggle_expert_takeover(self):
        """
        Only take effect whene vehicle num==1
        :return: None
        """
        self.current_track_vehicle.expert_takeover = not self.current_track_vehicle.expert_takeover

    def chase_camera(self) -> (str, BaseVehicle):
        if self.main_camera is None:
            return
        self.main_camera.reset()
        if self.config["prefer_track_agent"] is not None and self.config["prefer_track_agent"] in self.vehicles.keys():
            new_v = self.vehicles[self.config["prefer_track_agent"]]
            current_track_vehicle = new_v
        else:
            if self.main_camera.is_bird_view_camera():
                current_track_vehicle = self.current_track_vehicle
            else:
                vehicles = list(self.agent_manager.active_agents.values())
                if len(vehicles) <= 1:
                    return
                if self.current_track_vehicle in vehicles:
                    vehicles.remove(self.current_track_vehicle)
                new_v = get_np_random().choice(vehicles)
                current_track_vehicle = new_v
        self.main_camera.track(current_track_vehicle)
        return

    def bird_view_camera(self):
        self.main_camera.stop_track()

    def get_single_observation(self, vehicle_config: "Config") -> "ObservationType":
        if self.config["offscreen_render"]:
            o = ImageStateObservation(vehicle_config)
        else:
            o = LidarStateObservation(vehicle_config)
        return o

    def setup_engine(self):
        super(PGDriveEnv, self).setup_engine()
        # Press t can let expert take over. But this function is still experimental.
        self.engine.accept("t", self.toggle_expert_takeover)
        self.engine.accept("b", self.bird_view_camera)
        self.engine.accept("q", self.chase_camera)
        from pgdrive.manager.traffic_manager import TrafficManager
        self.engine.register_manager("traffic_manager", TrafficManager())


if __name__ == '__main__':

    def _act(env, action):
        assert env.action_space.contains(action)
        obs, reward, done, info = env.step(action)
        assert env.observation_space.contains(obs)
        assert np.isscalar(reward)
        assert isinstance(info, dict)

    env = PGDriveEnv()
    try:
        obs = env.reset()
        assert env.observation_space.contains(obs)
        _act(env, env.action_space.sample())
        for x in [-1, 0, 1]:
            env.reset()
            for y in [-1, 0, 1]:
                _act(env, [x, y])
    finally:
        env.close()
