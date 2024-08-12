import os
from typing import List

import nonebot
import yaml
from pydantic import BaseModel


config = {}  # 主进程全局配置，确保加载后读取


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
    nickname: list[str] = [f"灵温"]
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
        conf = yaml.load(f, Loader=yaml.FullLoader)
        config = conf
        if conf is None:
            nonebot.logger.warning(f"配置文件 {file} 为空，已创建默认配置，请修改后重启。")
            conf = BasicConfig().dict()
        return conf
