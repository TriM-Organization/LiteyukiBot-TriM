# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 LiteyukiStudio. All Rights Reserved 
#
# @Time    : 2024/7/22 上午11:25
# @Author  : snowykami
# @Email   : snowykami@outlook.com
# @File    : asa.py
# @Software: PyCharm
import asyncio

from liteyuki.plugin import PluginMetadata
from liteyuki import get_bot, logger
from liteyuki.comm.channel import get_channel

__plugin_meta__ = PluginMetadata(
    name="lifespan_monitor",
)

bot = get_bot()
nbp_chan = get_channel("nonebot-passive")
mbp_chan = get_channel("melobot-passive")


@bot.on_before_start
def _():
    logger.info("生命周期监控器：启动前")


@bot.on_before_shutdown
def _():
    print(get_channel("main"))
    logger.info("生命周期监控器：停止前")


@bot.on_before_restart
def _():
    logger.info("生命周期监控器：重启前")


@bot.on_after_start
def _():
    logger.info("生命周期监控器：启动后")


@bot.on_after_start
async def _():
    logger.info("生命周期监控器：启动后")



# @mbp_chan.on_receive()
# @nbp_chan.on_receive()
# async def _(data):
#     print("主进程收到数据", data)
