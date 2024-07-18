

import nonebot
from nonebot import require

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (
    on_alconna,
    Alconna,
    Subcommand,
    UniMessage,
    Option,
    store_true,
    Arparma,
)


musicreater_convert = on_alconna(
    aliases={"musicreater_convert","音乐转换","midi转换"},
    command=Alconna(
        "msctcvt",
        Option(
            "-r|--refresh",
            default=False,
            alias={"refr", "r", "刷新"},
            action=store_true,
        ),
        Subcommand(
            "memory",
            alias={"mem", "m", "内存"},
        ),
        Subcommand(
            "process",
            alias={"proc", "p", "进程"},
        ),
        # Subcommand(
        #     "refresh",
        #     alias={"refr", "r", "刷新"},
        # ),
    ),
)

