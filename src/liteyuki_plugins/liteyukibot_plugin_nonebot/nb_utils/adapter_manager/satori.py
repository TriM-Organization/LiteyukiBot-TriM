import json
import os

import nonebot
from nonebot.adapters import satori


def init(config: dict):
    if config.get("satori", None) is None:
        nonebot.logger.info("未寻得 Satori 设定信息，跳过初始化")
        return None
    satori_config = config.get("satori")
    if not satori_config.get("enable", False):
        nonebot.logger.info("Satori 未启用，跳过初始化")
        return None
    if os.getenv("SATORI_CLIENTS", None) is not None:
        nonebot.logger.info("Satori 客户端已在环境变量中配置，跳过初始化")
    os.environ["SATORI_CLIENTS"] = json.dumps(satori_config.get("hosts", []), ensure_ascii=False)
    config['satori_clients'] = satori_config.get("hosts", [])
    return


def register():
    if os.getenv("SATORI_CLIENTS", None) is not None:
        driver = nonebot.get_driver()
        driver.register_adapter(satori.Adapter)
