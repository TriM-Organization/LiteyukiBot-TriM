import sys

import nonebot

__NAME__ = "尹灵温|轻雪-睿乐"
__VERSION__ = "6.3.9"  # 60201

import requests

from src.utils.base.config import load_from_yaml, config
from src.utils.base.log import init_log
from git import Repo

major, minor, patch = map(int, __VERSION__.split("."))
__VERSION_I__ = 99000000 + major * 10000 + minor * 100 + patch


def init():
    """
    初始化
    Returns:

    """
    # 检测python版本是否高于3.10
    init_log()
    if sys.version_info < (3, 10):
        nonebot.logger.error(
            "此应用需要 Python3.10 以上的版本运行，你需要抱怨神羽的 Python 兼容性了。"
        )
        exit(1)

    try:
        # 检测git仓库
        repo = Repo(".")
    except Exception as e:
        nonebot.logger.error(
            f"无法读取 Git 仓库 `{e}`，你是否是从仓库直接下载的Zip文件？请使用git clone。"
        )

    # temp_data: TempConfig = common_db.where_one(TempConfig(), default=TempConfig())
    # temp_data.data["start_time"] = time.time()
    # common_db.save(temp_data)

    nonebot.logger.info(
        "正在 {} Python{}.{}.{} 上运行 尹灵温-NoneBot".format(
            sys.executable,
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro,
        )
    )
    nonebot.logger.info(
        "{} {}({}) 正在运行".format(__NAME__, __VERSION__, __VERSION_I__)
    )
