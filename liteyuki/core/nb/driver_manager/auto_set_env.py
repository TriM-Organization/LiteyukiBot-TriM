import os

import dotenv
import nonebot

from .defines import *


def auto_set_env(config: dict):
    dotenv.load_dotenv(".env")
    if os.getenv("DRIVER", None) is not None:
        nonebot.logger.info("Driver 已设入环境变量中，将跳过自动配置环节。")
        return
    if config.get("satori", {'enable': False}).get("enable", False):
        os.environ["DRIVER"] = get_driver_string(ASGI_DRIVER, HTTPX_DRIVER, WEBSOCKETS_DRIVER)
        nonebot.logger.info("已启用 Satori，将 driver 设为 ASGI+HTTPX+WEBSOCKETS")
    else:
        os.environ["DRIVER"] = get_driver_string(ASGI_DRIVER)
        nonebot.logger.info("已禁用 Satori，将 driver 设为 ASGI")
    return
