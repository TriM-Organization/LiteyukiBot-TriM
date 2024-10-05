import os

import dotenv
import nonebot

from .defines import *


def auto_set_env(config: dict):
    dotenv.load_dotenv(".env")
    if os.getenv("DRIVER", None) is not None:
        nonebot.logger.info("Driver 已在环境变量中配置，跳过自动设定")
        return
    if config.get("satori", {'enable': False}).get("enable", False):
        os.environ["DRIVER"] = get_driver_string(ASGI_DRIVER, HTTPX_DRIVER, WEBSOCKETS_DRIVER)
        nonebot.logger.info("启用 Satori，已设定 Driver 为 ASGI+HTTPX+WEBSOCKETS")
    else:
        os.environ["DRIVER"] = get_driver_string(ASGI_DRIVER)
        nonebot.logger.info("禁用 Satori，已设定 Driver 为 ASGI")
    return
