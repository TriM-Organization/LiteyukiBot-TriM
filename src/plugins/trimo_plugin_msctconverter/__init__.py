

from nonebot.plugin import PluginMetadata
from .msctexec import *
from .mspvexec import *

__author__ = "金羿Eilles"
__plugin_meta__ = PluginMetadata(
    name="伶伦转换器",
    description="",
    usage=(
            "MARKDOWN## 伶伦转换器\n"
            "《我的世界》音乐转换，结构生成与转换\n"
            "### 用法\n"
            "- `/msctcvt` 转换MIDI音乐\n"
        #     "- `/stctcvt` 各类结构互转\n"
        #     "- `/stctbld` 文本指令转结构\n"
        #     "- `/stctbld` 文本指令转结构\n"
    ),
    type="application",
    homepage="https://gitee.com/TriM-Organization/Musicreater",
    extra={
            "liteyuki": True,
            "toggleable"     : False,
            "default_enable" : True,
    }
)

