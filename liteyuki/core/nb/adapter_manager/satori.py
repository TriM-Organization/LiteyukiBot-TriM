import json
import os

import nonebot
from nonebot.adapters import satori


def init(config: dict):
    if config.get("satori", None) is None:
        nonebot.logger.info("未查见 Satori 的配置文档，将跳过 Satori 初始化")
        return None
    satori_config = config.get("satori")
    if not satori_config.get("enable", False):
        nonebot.logger.info("未启用 Satori ，将跳过 Satori 初始化")
        return None
    if os.getenv("SATORI_CLIENTS", None) is not None:
        nonebot.logger.info("Satori 客户端已设入环境变量，跳过此步。")
    os.environ["SATORI_CLIENTS"] = json.dumps(satori_config.get("hosts", []), ensure_ascii=False)
    config['satori_clients'] = satori_config.get("hosts", [])
    return


def register():
    if os.getenv("SATORI_CLIENTS", None) is not None:
        driver = nonebot.get_driver()
        driver.register_adapter(satori.Adapter)
