import random

import aiohttp
import zhDateTime

from src.utils import event as event_utils
from src.utils.base.language import get_user_lang, get_default_lang_code, Language
from src.utils.base.ly_typing import T_Bot, T_MessageEvent
from .api import *

require("nonebot_plugin_alconna")
from nonebot_plugin_alconna import (
    on_alconna,
    Alconna,
    Subcommand,
    UniMessage,
    Option,
    store_true,
    # AlconnaQuery,
    # Query,
    Arparma,
    Args,
)

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

status_alc = on_alconna(
    aliases={"状态"},
    command=Alconna(
        "status",
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

yanlun = on_alconna(
    aliases={"yanlun", "言·论", "yan_lun"},
    command=Alconna(
        "言论",
        Option(
            "-r|--refresh",
            default=False,
            alias={"刷新", "更新", "update"},
            action=store_true,
        ),
        Option("-c|--count", default=False, alias={"统计"}, action=store_true),
        Option("-l|--length", default=1.0, args=Args["length", float | int, 1.0]),
    ),
)


yanlun_path = "https://nd.liteyuki.icu/api/v3/share/content/Xpue?path=null"


# 每天4点更新
@scheduler.scheduled_job("cron", hour=4)
async def every_day_update():
    ulang = Language(get_default_lang_code(), "zh-WY")
    nonebot.logger.success(
        ulang.get("yanlun.refresh.success", COUNT=await update_yanlun())
    )


async def update_yanlun():

    global yanlun_texts, yanlun_seqs

    nonebot.logger.info("正在获取言·论信息")
    try:
        async with aiohttp.ClientSession() as client:
            resp = await client.get(yanlun_path)
            yanlun_texts = (await resp.text()).strip("\n").split("\n")
    except (ConnectionError, aiohttp.ClientError, aiohttp.WebSocketError) as err:
        nonebot.logger.warning("读取言·论信息发生 客户端或通道 错误：\n{}".format(err))
        yanlun_texts = ["以梦想为驱使 创造属于自己的未来"]
    # noinspection PyBroadException
    except BaseException as err:
        nonebot.logger.warning("读取言·论信息发生 未知 错误：\n{}".format(err))
        yanlun_texts = ["灵光焕发 深艺献心"]

    yanlun_seqs = yanlun_texts.copy()
    random.shuffle(yanlun_seqs)

    nonebot.logger.success("成功取得 言·论 {} 条".format(res := len(yanlun_texts)))

    return res


@nonebot.get_driver().on_startup
async def _():

    global yanlun_texts, yanlun_seqs

    solar_datetime = zhDateTime.DateTime.now()
    lunar_datetime = solar_datetime.to_lunar()
    solar_date = (solar_datetime.month, solar_datetime.day)
    lunar_date = (lunar_datetime.lunar_month, lunar_datetime.lunar_day)

    if solar_date == (4, 3):
        yanlun_seqs = yanlun_texts = ["金羿ELS 生日快乐~！", "Happy Birthday, Eilles!"]
    elif solar_date == (8, 6):
        yanlun_seqs = yanlun_texts = [
            "诸葛亮与八卦阵 生日快乐~！",
            "Happy Birthday, bgArray~!",
        ]
    elif solar_date == (8, 16):
        yanlun_seqs = yanlun_texts = [
            "鱼旧梦 生日快乐~！",
            "Happy Birthday, ElapsingDreams~!",
        ]
    else:
        await update_yanlun()


def random_yanlun_text() -> str:
    global yanlun_texts, yanlun_seqs
    if not yanlun_seqs:
        yanlun_seqs = yanlun_texts.copy()
        random.shuffle(yanlun_seqs)
    return yanlun_seqs.pop()


def random_yanlun() -> tuple:
    seq = random_yanlun_text().replace("    ", "\t").split("\t——", 1)
    return seq[0], "" if len(seq) == 1 else seq[1]


status_card_cache = {}  # lang -> bytes


@status_alc.handle()
async def _(
    result: Arparma,
    event: T_MessageEvent,
    bot: T_Bot,
    # refresh: Query[bool] = AlconnaQuery("refresh.value", False),
):
    ulang = get_user_lang(event_utils.get_user_id(event))  # type: ignore
    global status_card_cache
    if (
        result.options["refresh"].value
        or ulang.lang_code not in status_card_cache.keys()
        or (
            ulang.lang_code in status_card_cache.keys()
            and time.time() - status_card_cache[ulang.lang_code][1] > 300  # 缓存
        )
    ):
        status_card_cache[ulang.lang_code] = (
            await generate_status_card(
                bot=await get_bots_data(),
                hardware=await get_hardware_data(),
                liteyuki=await get_liteyuki_data(),
                lang=ulang.lang_code,
                motto=dict(zip(["text", "source"], random_yanlun())),
                bot_id=bot.self_id,
            ),
            time.time(),
        )
    image = status_card_cache[ulang.lang_code][0]
    await status_alc.finish(UniMessage.image(raw=image))


@status_alc.assign("memory")
async def _():
    pass


@status_alc.assign("process")
async def _():
    pass


@yanlun.handle()
async def _(
    result: Arparma,
    event: T_MessageEvent,
    bot: T_Bot,
    # refresh: Query[bool] = AlconnaQuery("refresh.value", False),
    # count: Query[bool] = AlconnaQuery("count.value", False),
):
    # print(result.options)
    ulang = get_user_lang(event_utils.get_user_id(event))  # type: ignore
    if result.options["refresh"].value:
        await yanlun.send(
            UniMessage.text(
                ulang.get("yanlun.refresh.success", COUNT=await update_yanlun())
            )
        )
    if result.options["count"].value:
        authors = [
            (
                ("B站")
                if ("\t——B站" in i.upper() or "    ——B站" in i.upper())
                else (
                    i.split("\t——")[1].replace(" ", "")
                    if "\t——" in i
                    else (
                        i.split("    ——")[1].replace(" ", "")
                        if "    ——" in i
                        else ("MYH")
                    )
                )
            )
            for i in yanlun_texts
        ]

        total = len(yanlun_texts)

        chart = sorted(
            [(i, authors.count(i)) for i in set(authors)],
            key=lambda x: x[1],
            reverse=True,
        )

        await yanlun.send(
            UniMessage.text(
                ulang.get("yanlun.count.head").replace("ttt", "\t")
                + "\n"
                + "".join(
                    [
                        (
                            "{}\t{}({}%)\n".format(
                                aut, cnt, int(cnt * 10000 / total + 0.5) / 100
                            )
                            if cnt * 100 / total >= chart[10][1] * 100 / total
                            else ""
                        )
                        for aut, cnt in chart
                    ]
                )
                + ulang.get("yanlun.count.tail", NUM=total)
            )
        )

    final_length = 0
    try:
        final_length += result.options["length"].args["length"]
    except:
        final_length = 1

    (
        (
            await yanlun.finish(
                UniMessage.text(
                    "\n".join([random_yanlun_text() for i in range(iill)])
                    if iill <= 100
                    else ulang.get("yanlun.length.toolong")
                )
            )
            if iill > 0
            else await yanlun.finish(
                UniMessage.text(ulang.get("yanlun.length.tooshort"))
            )
        )
        if (iill := int(final_length)) == final_length
        else await yanlun.finish(UniMessage.text(ulang.get("yanlun.length.float")))
    )


time_query = on_alconna(
    command=Alconna(
        "时间",
    ),
    aliases={"时间查询", "timeq", "timequery"},
)


@time_query.handle()
async def _(
    event: T_MessageEvent,
    bot: T_Bot,
):
    # ulang = get_user_lang(event_utils.get_user_id(event))  # type: ignore
    await time_query.finish(
        UniMessage.text(zhDateTime.DateTime.now().to_lunar().hanzify())
    )
