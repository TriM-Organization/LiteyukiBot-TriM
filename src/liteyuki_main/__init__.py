from nonebot.plugin import PluginMetadata

from .core import *
from .loader import *
from .dev import *

__author__ = "snowykami"
__plugin_meta__ = PluginMetadata(
    name="轻雪核心插件",
    description="轻雪主程序插件，包含了许多初始化的功能",
    usage="",
    homepage="https://github.com/snowykami/LiteyukiBot",
    extra={
        "liteyuki": True,
        "toggleable": False,
    },
)

from ..utils.base.language import Language, get_default_lang_code

print(
    "\033[34m"
    + r"""
 ▅▅▅▅▅▅▅▅▅▅▅▅▅▅██ ▅▅▅▅▅▅▅▅▅▅▅▅▅▅██   ██  ▅▅▅▅▅▅▅▅▅▅█™
 ▛     ██      ██ ▛             ██  ███  ██        ██
       ██      ██  ███████████████   ██  ████████▅ ██
  ███████████████               ██ ███   ██        ██
       ██      ██ ▅██████████████▛  ██   ████████████
       ██      ██       ███         ███    
 ████████████████  ██▅  ███    ██       ▅▅▅▅▅▅▅▅▅▅▅██
      ███       █   ▜███████  ██    ███  ██ ██  ██ ██
     ███              ███ █████▛    ██   ██ ██  ██ ██
   ███               ██    ███   █  ██   ██ ██  ██ ██
  ███            █████      ██████ ███  ██████████████
                               商标标记 © 2024 金羿Eilles
             版权所有 © 2020-2024 神羽SnowyKami & 金羿Eilles\\
                        with LiteyukiStudio & TriM Org.
                                             保留所有权利
"""
    + "\033[0m"
)


sys_lang = Language(get_default_lang_code())
nonebot.logger.info(
    sys_lang.get("main.current_language", LANG=sys_lang.get("language.name"))
)
