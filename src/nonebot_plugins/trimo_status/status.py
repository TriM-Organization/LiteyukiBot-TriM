import random

from typing import Dict, List, Tuple, Optional

import aiohttp
import zhDateTime
from nonebot import require

from src.utils import event as event_utils
from src.utils.base.language import get_user_lang, get_default_lang_code, Language
from src.utils.base.ly_typing import T_Bot, T_MessageEvent
from src.utils.io import read_file

from .config import status_config
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

WESTERN_DATE_EVENT_YANLUN: Dict[Tuple[Tuple[int, int], ...], List[str]] = {
    ((4, 3),): ["金羿 生日快乐~！", "Happy Birthday, Eilles!"],
    ((8, 6),): ["玉衡 生日快乐~！", "Happy Birthday, Alioth~!"],
    ((8, 16),): ["鱼旧梦 生日快乐~！", "Happy Birthday, ElapsingDreams~!"],
    ((7, 12), (5, 21)): ["华风夏韵 洛水天依"],
    ((8, 31),): ["初始之音 响彻未来"],
    ((2, 10),): ["桃之夭夭 灼灼其華"],
    ((4, 12),): ["乐正司百曲 绫动万年红"],
    ((10, 2),): ["龙翼振风雨 牙音彻天明"],
    ((2, 21), (8, 12)): ["众星因你 皆降为尘", "浩瀚众星 皆降为尘"],
    ((7, 11),): ["言出一人歌 歌起万人和"],
    ((5, 20),): ["沾以清墨 书我弦歌"],
    ((12, 10),): ["徵音飞羽 一梦南柯"],
}

CHINESE_DATE_EVENT_YANLUN: Dict[Tuple[Tuple[int, int], ...], List[str]] = {
    ((1, 1),): [
        "新春快乐~",
        "千门万户曈曈日，总把新桃换旧符\t——王安石《元日》",
        "爆竹声中一岁除，春风送暖入屠苏\t——王安石《元日》",
        "半盏屠苏犹未举，灯前小草写桃符\t—— 陆游《除夜雪》",
        "愿得长如此，年年物候新\t—— 卢照邻《元日述怀》",
    ]
}


async def update_yanlun():
    global yanlun_texts, yanlun_seqs

    nonebot.logger.info("正在获取言·论信息")

    if status_config.yanlun_type == "url":
        try:
            async with aiohttp.ClientSession() as client:
                resp = await client.get(status_config.yanlun_path, timeout=15)
                yanlun_texts = (await resp.text()).strip("\n").split("\n")
        except (ConnectionError, aiohttp.ClientError, aiohttp.WebSocketError) as err:
            nonebot.logger.warning("读取言·论信息发生网络连接错误：\n{}".format(err))
            yanlun_texts = ["以梦想为驱使 创造属于自己的未来"]
        # noinspection PyBroadException
        except BaseException as err:
            nonebot.logger.warning("读取言·论信息发生未知错误：\n{}".format(err))
            yanlun_texts = ["灵光焕发 深艺献心"]
    elif status_config.yanlun_type == "file":
        try:
            yanlun_texts = (
                (await read_file(status_config.yanlun_path, "r", encoding="utf-8"))
                .strip("\n")
                .split("\n")
            )
        except BaseException as err:
            nonebot.logger.warning(
                "读取言·论信息发生文件输入输出错误：\n{}".format(err)
            )
            yanlun_texts = ["山高水长 日月圆缺"]

    yanlun_seqs = yanlun_texts.copy()
    random.shuffle(yanlun_seqs)

    nonebot.logger.success("成功取得 言·论 {} 条".format(res := len(yanlun_texts)))

    return res


async def auto_update_yanlun() -> int:

    global yanlun_texts, yanlun_seqs

    western_datetime = zhDateTime.DateTime.now()
    chinese_datetime = western_datetime.chinesize
    western_date = (western_datetime.month, western_datetime.day)
    chinese_date = (
        chinese_datetime.chinese_calendar_month,
        chinese_datetime.chinese_calendar_day,
    )

    yanlun_texts = []

    for dates, yanlun in WESTERN_DATE_EVENT_YANLUN.items():
        if western_date in dates:
            yanlun_texts.extend(yanlun)

    for dates, yanlun in CHINESE_DATE_EVENT_YANLUN.items():
        if chinese_date in dates:
            yanlun_texts.extend(yanlun)

    if yanlun_texts:
        yanlun_seqs = yanlun_texts.copy()
        return len(yanlun_texts)
    else:
        return await update_yanlun()


# 启动时更新
@nonebot.get_driver().on_startup
async def _():
    ulang = Language(get_default_lang_code(), "zh-CN")
    nonebot.logger.success(
        ulang.get("yanlun.refresh.success", COUNT=await auto_update_yanlun())
    )


# 每天4点更新
@scheduler.scheduled_job("cron", hour=4)
async def _():
    ulang = Language(get_default_lang_code(), "zh-CN")
    nonebot.logger.success(
        ulang.get("yanlun.refresh.success", COUNT=await auto_update_yanlun())
    )


def random_yanlun_text() -> str:
    global yanlun_texts, yanlun_seqs
    if not yanlun_seqs:
        yanlun_seqs = yanlun_texts.copy()
        random.shuffle(yanlun_seqs)
    return yanlun_seqs.pop()


def random_yanlun() -> tuple:
    seq = random_yanlun_text().replace("    ", "\t").split("\t——", 1)
    return seq[0], "" if len(seq) == 1 else seq[1]


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
        Option(
            "-t|-md|--markdown",
            default=False,
            # alias={"refr", "r", "刷新"},
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
            (
                await generate_status_card_markdown(
                    bot=await get_bots_data(),
                    hardware=await get_hardware_data(ulang.lang_code),
                    liteyuki=await get_liteyuki_data(),
                    lang=ulang.lang_code,
                    motto=dict(zip(["text", "source"], random_yanlun())),
                )
                if result.options["markdown"].value
                else (
                    await generate_status_card(
                        bot=await get_bots_data(),
                        hardware=await get_hardware_data(ulang.lang_code),
                        liteyuki=await get_liteyuki_data(),
                        lang=ulang.lang_code,
                        motto=dict(zip(["text", "source"], random_yanlun())),
                        bot_id=bot.self_id,
                    )
                )
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
        Option("-s|--special", default=False, action=store_true),
        Option("-c|--count", default=False, alias={"统计"}, action=store_true),
        Option("-l|--length", default=1.0, args=Args["length", float | int, 1.0]),
    ),
)


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
                ulang.get(
                    "yanlun.refresh.success",
                    COUNT=(
                        (await auto_update_yanlun())
                        if result.options["special"].value
                        else (await update_yanlun())
                    ),
                )
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
        UniMessage.text(zhDateTime.DateTime.now().chinesize.chinese_text)
    )


number_read = on_alconna(
    command=Alconna(
        "读数",
        Option("-g|--group", default=False, action=store_true),
        Args["number", str],
    ),
    aliases={"readout_number", "number_read"},
)

@number_read.handle()
async def _(
    event: T_MessageEvent,
    bot: T_Bot,
    result: Arparma,
):
    num = result.main_args.get("number", "")
    try:
        num = int(num)
    except:
        await number_read.finish(UniMessage.text("小数点后直接读，不是数字没法读"))
    
    if num < 0:
        result_readout = "负"
        num = abs(num)
    else:
        result_readout = ""

    try:
        if result.options["group"].value:
            result_readout += zhDateTime.int_2_grouped_han_str(num)
        else:
            result_readout += zhDateTime.int_hanzify(num)
    except IndexError as e:
        await number_read.finish(UniMessage.text("数字太大了：{e}".format(e)))

    await number_read.finish(UniMessage.text(result_readout))