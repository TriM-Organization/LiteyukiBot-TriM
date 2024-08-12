# -*- coding: utf-8 -*-
"""
Copyright (C) 2020-2024 LiteyukiStudio. All Rights Reserved 

@Time    : 2024/8/10 下午11:25
@Author  : snowykami
@Email   : snowykami@outlook.com
@File    : register_service.py
@Software: PyCharm
"""
import json
import os.path
import platform

import requests
from git import Repo
from liteyuki.plugin import PluginMetadata
from liteyuki import get_bot, logger

__plugin_meta__ = PluginMetadata(
    name="注册服务",
)

liteyuki = get_bot()
commit_hash = Repo(".").head.commit.hexsha


def register_bot():
    url = "https://api.liteyuki.icu/register"
    data = {
            "name"     : "尹灵温|轻雪-睿乐",
            "version"  : "即时更新",
            "hash"     : commit_hash,
            "version_i": 99,
            "python"   : f"{platform.python_implementation()} {platform.python_version()}",
            "os"       : f"{platform.system()} {platform.version()} {platform.machine()}"
    }
    try:
        logger.info("正在等待 Liteyuki 注册服务器……")
        resp = requests.post(url, json=data, timeout=(10, 15))
        if resp.status_code == 200:
            data = resp.json()
            if liteyuki_id := data.get("liteyuki_id"):
                with open("data/liteyuki/liteyuki.json", "wb") as f:
                    f.write(json.dumps(data).encode("utf-8"))
                logger.success("成功将 {} 注册到 Liteyuki 服务器".format(liteyuki_id))
            else:
                raise ValueError(f"无法向 Liteyuki 服务器注册：{data}")

    except Exception as e:
        logger.warning(f"虽然向 Liteyuki 服务器注册失败，但无关紧要：{e}")


@liteyuki.on_before_start
async def _():
    if not os.path.exists("data/liteyuki/liteyuki.json"):
        register_bot()
