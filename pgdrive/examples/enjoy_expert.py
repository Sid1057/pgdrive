"""
Please feel free to run this script to enjoy a journey carrying out by a professional driver!
Our expert can drive in 10000 maps with almost 90% likelihood to achieve the destination.

Note: This script require rendering, please following the installation instruction to setup a proper
environment that allows popping up an window.
"""
import random

from pgdrive import PGDriveEnvV2
from pgdrive.examples import expert, get_terminal_state

if __name__ == '__main__':
    env = PGDriveEnvV2(dict(use_render=False, environment_num=100, start_seed=random.randint(0, 1000)))
    obs = env.reset()
    success_list, reward_list, ep_reward, ep_len, ep_count = [], [], 0, 0, 0
    try:
        while True:
            action = expert(obs)
            obs, reward, done, info = env.step(action)
            ep_reward += reward
            ep_len += 1
            env.render(

                show_agent_name=False,
                # film_size=(4000, 4000),
                # film_size=(2100, 2100),
                # screen_size=(2000, 2000),

                mode="top_down",
                road_color=(35, 35, 35),
                track=True,

                num_stack=30,

                # draw_dead=False

                # zoomin=2.0,

            )
            if done:
                ep_count += 1
                success_list.append(1 if get_terminal_state(info) == "Success" else 0)
                reward_list.append(ep_reward)
                print(
                    "{} episodes terminated! Length: {}, Reward: {:.4f}, Terminal state: {}.".format(
                        ep_count, ep_len, ep_reward, get_terminal_state(info)
                    )
                )
                ep_reward = 0
                ep_len = 0
                obs = env.reset()
    finally:
        print("Closing the environment!")
        env.close()
        success_rate = sum(success_list) / len(success_list) if len(success_list) > 0 else 0
        mean_reward = sum(reward_list) / len(reward_list) if len(reward_list) > 0 else 0
        print("Episode count {}, Success rate: {}, Average reward: {}".format(ep_count, success_rate, mean_reward))
