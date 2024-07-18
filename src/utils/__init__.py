import json
import os.path
import platform
import sys
import time

import nonebot

__NAME__ = "LiteyukiBot-Trim"
__VERSION__ = "6.3.3"  # 60201
# __VERSION_I__ = 99060303

import requests

from src.utils.base.config import load_from_yaml, config
from src.utils.base.log import init_log
from src.utils.base.data_manager import TempConfig, auto_migrate, common_db
from git import Repo


major, minor, patch = map(int, __VERSION__.split("."))
__VERSION_I__ = 99000000 + major * 10000 + minor * 100 + patch


def register_bot():
    url = "https://api.liteyuki.icu/register"
    data = {
        "name": __NAME__,
        "version": __VERSION__,
        "version_i": __VERSION_I__,
        "python": f"{platform.python_implementation()} {platform.python_version()}",
        "os": f"{platform.system()} {platform.version()} {platform.machine()}",
    }
    try:
        nonebot.logger.info("正在等待 Liteyuki 注册服务器…")
        resp = requests.post(url, json=data, timeout=(10, 15))
        if resp.status_code == 200:
            data = resp.json()
            if liteyuki_id := data.get("liteyuki_id"):
                with open("data/liteyuki/liteyuki.json", "wb") as f:
                    f.write(json.dumps(data).encode("utf-8"))
                nonebot.logger.success(f"成功将 {liteyuki_id} 注册到 Liteyuki 服务器")
            else:
                raise ValueError(f"无法向 Liteyuki 服务器注册：{data}")

    except Exception as e:
        nonebot.logger.warning(f"向 Liteyuki 服务器注册失败，但无所谓：{e}")


def init():
    """
    初始化
    Returns:

    """
    # 检测python版本是否高于3.10
    auto_migrate()
    init_log()
    if sys.version_info < (3, 10):
        nonebot.logger.error(
            "此应用需要 Python3.10 以上的版本运行，你需要更新自己的 Python 运行环境了。"
        )
        exit(1)

    try:
        # 检测git仓库
        repo = Repo(".")
    except Exception as e:
        nonebot.logger.error(
            f"无法读取 Git 仓库 {e}，你是否是从仓库内下载的Zip文件？请使用git clone。"
        )

    temp_data: TempConfig = common_db.where_one(TempConfig(), default=TempConfig())  # type: ignore
    temp_data.data["start_time"] = time.time()
    common_db.save(temp_data)

    # 在加载完成语言后再初始化日志
    nonebot.logger.info("尹灵温 正在初始化…")

    if not os.path.exists("data/liteyuki/liteyuki.json"):
        register_bot()

    if not os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            f.write("[tool.nonebot]\n")

    nonebot.logger.info(
        f"正在 {sys.executable} Python{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} 上运行 尹灵温"
    )
    nonebot.logger.info(f"{__NAME__} {__VERSION__}({__VERSION_I__}) 正在运行")
