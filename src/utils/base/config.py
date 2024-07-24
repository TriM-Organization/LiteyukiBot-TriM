import os
from typing import List

import nonebot
import yaml
from pydantic import BaseModel

from .data_manager import StoredConfig, TempConfig, common_db
from .ly_typing import T_Bot
from ..message.tools import random_hex_string

config = {}  # 全局配置，确保加载后读取


class SatoriNodeConfig(BaseModel):
    host: str = ""
    port: str = "5500"
    path: str = ""
    token: str = ""


class SatoriConfig(BaseModel):
    comment: str = "此皆正处于开发之中，切勿在生产环境中启用。"
    enable: bool = False
    hosts: List[SatoriNodeConfig] = [SatoriNodeConfig()]


class BasicConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 20247
    superusers: list[str] = []
    command_start: list[str] = ["/", ""]
    nickname: list[str] = [f"灵温-{random_hex_string(6)}"]
    satori: SatoriConfig = SatoriConfig()
    data_path: str = "data/liteyuki"


def load_from_yaml(file: str) -> dict:
    global config
    nonebot.logger.debug("Loading config from %s" % file)
    if not os.path.exists(file):
        nonebot.logger.warning(f"未找到配置文件 {file} ，已创建默认配置，请修改后重启。")
        with open(file, "w", encoding="utf-8") as f:
            yaml.dump(BasicConfig().dict(), f, default_flow_style=False)

    with open(file, "r", encoding="utf-8") as f:
        conf = init_conf(yaml.load(f, Loader=yaml.FullLoader))
        config = conf
        if conf is None:
            nonebot.logger.warning(f"配置文件 {file} 为空，已创建默认配置，请修改后重启。")
            conf = BasicConfig().dict()
        return conf


def get_config(key: str, default=None):
    """获取配置项，优先级：bot > config > db > yaml"""
    try:
        bot = nonebot.get_bot()
    except:
        bot = None

    if bot is None:
        bot_config = {}
    else:
        bot_config = bot.config.dict()

    if key in bot_config:
        return bot_config[key]

    elif key in config:
        return config[key]

    elif key in common_db.where_one(StoredConfig(), default=StoredConfig()).config:
        return common_db.where_one(StoredConfig(), default=StoredConfig()).config[key]

    elif key in load_from_yaml("config.yml"):
        return load_from_yaml("config.yml")[key]

    else:
        return default


def set_stored_config(key: str, value):
    temp_config: TempConfig = common_db.where_one(TempConfig(), default=TempConfig())
    temp_config.data[key] = value
    common_db.save(temp_config)


def init_conf(conf: dict) -> dict:
    """
    初始化配置文件，确保配置文件中的必要字段存在，且不会冲突
    Args:
        conf:

    Returns:

    """
    # 若command_start中无""，则添加必要命令头，开启alconna_use_command_start防止冲突
    # 以下内容由于issue #53 被注释
    # if "" not in conf.get("command_start", []):
    #     conf["alconna_use_command_start"] = True
    return conf
    pass
