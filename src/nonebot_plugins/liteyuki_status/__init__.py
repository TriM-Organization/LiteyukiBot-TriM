from nonebot.plugin import PluginMetadata
from .status import *

__author__ = "神羽SnowyKami & 金羿Eilles"
__plugin_meta__ = PluginMetadata(
    name="灵温状态查看",
    description="",
    usage=(
        "MARKDOWN### 状态查看器\n"
        "查看机器人的状态\n"
        "### 用法\n"
        "- `/status` 查看基本情况\n"
        "- `/status -r` 强制刷新状态情况\n"
        "- `/status -d` 使用简化markdown渲染状态\n"
    ),
    type="application",
    homepage="https://gitee.com/TriM-Organization/LiteyukiBot-TriM",
    extra={
        "liteyuki": True,
        "toggleable": False,
        "default_enable": True,
    },
)
