# -*- coding: utf-8 -*-
"""
NoneBot 开发环境重载监视器
"""
import os.path

from liteyuki.dev import observer
from liteyuki import get_bot, logger
from liteyuki.utils import IS_MAIN_PROCESS
from watchdog.events import FileSystemEvent


liteyuki = get_bot()

exclude_extensions = (".pyc", ".pyo")


@observer.on_file_system_event(
    directories=("src/nonebot_plugins",),
    event_filter=lambda event: not event.src_path.endswith(exclude_extensions) and ("__pycache__" not in event.src_path ) and os.path.isfile(event.src_path)
)
def restart_nonebot_process(event: FileSystemEvent):
    logger.debug(f"文件 {event.src_path} 已更新，正在重载 nonebot")
    liteyuki.restart_process("nonebot")