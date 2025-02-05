import logging
import os
import pathlib
import sys

from pgdrive.utils.utils import is_win


class AssetLoader:
    """
    Load model for each element when render is needed.
    """
    loader = None
    asset_path = None

    @staticmethod
    def init_loader(engine):
        """
        Due to the feature of Panda3d, keep reference of loader in static variable
        """
        root_path = pathlib.PurePosixPath(__file__).parent.parent if not is_win() else pathlib.Path(__file__).resolve(
        ).parent.parent
        AssetLoader.asset_path = root_path.joinpath("assets")
        if engine.win is None:
            logging.debug("Physics world mode")
            return
        logging.debug("Onscreen/Offscreen mode, Render/Load Elements")
        AssetLoader.loader = engine.loader

    @classmethod
    def get_loader(cls):
        assert AssetLoader.loader, "Please initialize AssetLoader before getting it!"
        return cls.loader

    @staticmethod
    def windows_style2unix_style(win_path):
        path = win_path.as_posix()
        panda_path = "/" + path[0].lower() + path[2:]
        return panda_path

    @staticmethod
    def file_path(*path_string):
        """
        Usage is the same as path.join(dir_1,dir_2,file_name)
        :param path_string: a tuple
        :return: file path used to load asset
        """
        path = AssetLoader.asset_path.joinpath(*path_string)
        return AssetLoader.windows_style2unix_style(path) if sys.platform.startswith("win") else str(path)

    @classmethod
    def load_model(cls, file_path):
        """
        A quick load method
        :param file_path: path in string, usually use the return value of AssetLoader.file_path()
        :return: model node path
        """
        assert cls.loader is not None
        return cls.loader.loadModel(file_path)

    @classmethod
    def initialized(cls):
        return cls.asset_path is not None


def initialize_asset_loader(engine):
    # load model file in utf-8
    os.environ["PYTHONUTF8"] = "on"
    if AssetLoader.initialized():
        logging.warning(
            "AssetLoader is initialize to root path: {}! But you are initializing again!".format(
                AssetLoader.asset_path
            )
        )
        return
    AssetLoader.init_loader(engine)


def close_asset_loader():
    cls = AssetLoader
    cls.loader = None
    cls.asset_path = None
