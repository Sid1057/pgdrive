import os
import sys

from PIL import Image
from panda3d.core import PNMImage, loadPrcFileData

from pgdrive.envs.pgdrive_env import PGDriveEnv


def capture_image(headless):
    env = PGDriveEnv(
        dict(
            use_render=False,
            start_seed=666,
            traffic_density=0.1,
            offscreen_render=True,
            headless_machine_render=headless
        )
    )
    env.reset()
    for i in range(10):
        env.step([0, 1])
    img = PNMImage()
    env.engine.win.getScreenshot(img)
    img.write("vis_installation.png")
    env.close()
    if not headless:
        im = Image.open("vis_installation.png")
        im.show()
        os.remove("vis_installation.png")
        print("Offscreen render launched successfully! \n ")
    else:
        print(
            "Headless mode Offscreen render launched successfully! \n "
            "A image named \'tset_install.png\' is saved. Open it to check if offscreen mode works well"
        )


def vis_installation(headless=True):
    loadPrcFileData("", "notify-level-task fatal")
    try:
        env = PGDriveEnv({"use_render": False, "offscreen_render": False})
        env.reset()
        for i in range(1, 100):
            o, r, d, info = env.step([0, 1])
        env.close()
        del env
    except:
        print("Error happens in Bullet physics world !")
        sys.exit()
    else:
        print("Bullet physics world is launched successfully!")
    try:
        capture_image(headless)
    except:
        print("Error happens when drawing scene in offscreen mode!")


if __name__ == "__main__":
    vis_installation(False)
