import os
import sys
import json
import random
import shutil

import asyncio

from io import StringIO
from pathlib import Path
from typing import Annotated, Any, Union, Literal
from types import EllipsisType

# from nonebot import require

import aiohttp
import zhDateTime
import Musicreater

import Musicreater.plugin.archive
from Musicreater.plugin.bdxfile import to_BDX_file_in_delay, to_BDX_file_in_score
from Musicreater.plugin.addonpack import (
    to_addon_pack_in_delay,
    # to_addon_pack_in_repeater,
    to_addon_pack_in_score,
)
from Musicreater.plugin.mcstructfile import (
    to_mcstructure_file_in_delay,
    # to_mcstructure_file_in_repeater,
    to_mcstructure_file_in_score,
)

# import Musicreater.types
# import Musicreater.subclass
# import Musicreater.constants

import nonebot
import nonebot.adapters
import nonebot.drivers
import nonebot.rule

# from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.event import (
    GroupUploadNoticeEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from src.utils.base.ly_typing import T_Bot, T_MessageEvent

from src.utils import event as event_utils
from src.utils.base.language import get_user_lang

# from src.utils.base.config import get_config
from src.utils.message.message import MarkdownMessage
from src.utils.message.html_tool import md_to_pic
from src.utils.message.tools import random_hex_string

from .execute_auto_translator import auto_translate  # type: ignore
from .utils import hanzi_timeid

nonebot.require("nonebot_plugin_alconna")
nonebot.require("nonebot_plugin_apscheduler")


from nonebot_plugin_alconna import (
    on_alconna,
    Alconna,
    # Subcommand,
    UniMessage,
    Option,
    store_true,
    # store_false,
    # store_value,
    Arparma,
    Args,
)

from nonebot_plugin_apscheduler import scheduler


from ..liteyuki_status.status import random_yanlun_text

(config_dir := Path(__file__).parent / "config").mkdir(exist_ok=True)
(database_dir := Path(__file__).parent / "db").mkdir(exist_ok=True)
temporary_dir = Path(__file__).parent / "temp"


if (config_path := config_dir / "config.json").exists():
    configdict: dict = json.load(config_path.open("r", encoding="utf-8"))
else:
    configdict = {
        "donateCodePath": "https://foruda.gitee.com/images/1690165328188128032/d7f24fb5_9911226.jpeg",
        "donateSite": "",
        "helpPicPath": "https://foruda.gitee.com/images/1685873169584963569/95fe9b0b_9911226.png",
        "maxCacheSize": 1048576,
        "maxCacheTime": {".mcfunction": 900, ".mid .midi": 1800, ".json": 1800},
        "maxSingleFileSize": {
            ".mcfunction": 524288,
            ".mid .midi": 131072,
            ".json": 8192,
        },
        "maxPersonConvert": {
            "music": 25,
            "structure": 20,
        },
    }


if (saves_path := database_dir / "file_saver.json").exists():
    filesaves: dict = json.load(saves_path.open("r", encoding="utf-8"))
else:
    filesaves = {}

max_cache_size = configdict["maxCacheSize"]
cache_limit_data: dict[str, tuple[int, int]] = {}

for cache_subtype in configdict["maxCacheTime"].keys():
    for i in cache_subtype.split(" "):
        cache_limit_data[i] = (
            configdict["maxSingleFileSize"][cache_subtype],
            configdict["maxCacheTime"][cache_subtype],
        )


# if not os.path.exists("./temp/"):
#     os.makedirs("./temp/")


def save_configdict():
    json.dump(
        configdict,
        config_path.open("w", encoding="utf-8"),
        indent=4,
        ensure_ascii=False,
        sort_keys=True,
    )


def save_filesaves():
    json.dump(
        filesaves,
        saves_path.open("w", encoding="utf-8"),
        indent=4,
        ensure_ascii=False,
        sort_keys=True,
    )


save_configdict()
save_filesaves()

enable_auto_exe_translate = {}

people_convert_point: dict[str, dict[str, float]] = {}


def query_convert_points(
    usr_id: str, item: str, decline: float = 0
) -> tuple[bool, float]:
    """
    查询用户是否拥有足够的点数，若拥有则消耗，若不足则返回False

    参数：
    usr_id: str
        用户id
    item: str
        要消耗的点数类型
    decline: float
        消耗点数数量
    store: Any
        要储存的数据

    返回：
    tuple[bool, float]
        是否足够和剩余点数
    """
    global people_convert_point
    if usr_id not in people_convert_point:
        people_convert_point[usr_id] = {item: configdict["maxPersonConvert"][item]}
    if item not in people_convert_point[usr_id]:
        people_convert_point[usr_id][item] = configdict["maxPersonConvert"][item]

    if people_convert_point[usr_id][item] >= decline:
        people_convert_point[usr_id][item] -= decline
        return True, people_convert_point[usr_id][item]
    else:
        return False, people_convert_point[usr_id][item]


something_temporary: dict[
    str,
    dict[
        Literal["stuff", "time"],
        Union[Path | os.PathLike[str] | str, tuple[Any, str]] | int,
    ],
] = {}


def add_file_to_delete(file_: Path | os.PathLike[str] | str, wait_p30s: int = 0) -> str:
    """
    增加一个地址，过会儿删除这个地址指向的文件

    参数：
    file_: Path | os.PathLike[str] | str
        文件路径
    wait_p30s: int
        等待时间，单位为 30 秒内（不大于 30 秒），默认为 `0`

    返回：
    str
        文件路径的字符串
    """
    global something_temporary
    something_temporary[rr := str(file_)] = {"stuff": file_, "time": wait_p30s}
    return rr


def add_memory_to_temporary(
    index: str, memory_: Any, description: str = "一个内存", wait_p30s: int = 0
) -> None:
    """
    向临时内存存储中填入内存信息

    参数：
    index: str
        索引
    memory_: Any
        内存
    description: str
        内存描述
    wait_p30s: int
        等待时间，单位为 30 秒内（不大于 30 秒），默认为 `0`
    """
    global something_temporary
    something_temporary[index] = {"stuff": (memory_, description), "time": wait_p30s}


def read_memory_from_temporary(index: str) -> Any:
    """
    从临时内存存储中读取内容

    参数：
    index: str
        索引

    返回：
    Any
        内容，当无此内容时返回 `None`
    """
    global something_temporary
    memory_cmp = something_temporary.get(index, {"stuff": None})["stuff"]
    if isinstance(memory_cmp, tuple):
        return memory_cmp[0]
    else:
        return memory_cmp


def get_stored_path(
    user_id: str, item: Union[Path, os.PathLike[str], str], superuser: bool = False
) -> Path:
    """
    获取用户文件存储路径

    参数：
    user_id: str
        用户id
    item: Union[Path, os.PathLike[str], str]
        文件名（对于用户目录的相对路径）
    superuser: bool
        是否为超级用户，默认为 `False` 若为 `True` 则在用户文件中寻找

    返回：
    Path
        文件路径
    """

    if not isinstance(item, Path):
        item_ = Path(item).name
    else:
        item_ = item.name

    result_dest = database_dir / user_id / item_

    if not result_dest.exists() and superuser:
        for usr_id_ in filesaves.keys():
            if (result_dest_ := database_dir / usr_id_ / item_).exists():
                result_dest = result_dest_
                break

    return result_dest


# 每天4点更新
@scheduler.scheduled_job("cron", hour=4)
async def every_day_update():
    # ulang = Language(get_default_lang_code(), "zh-WY")
    global people_convert_point
    people_convert_point = {}
    nonebot.logger.success("已重置每日转换次数")


@nonebot.get_driver().on_startup
async def _():
    nonebot.logger.info("正在删除临时文件目录")
    while temporary_dir.exists():
        await asyncio.sleep(1)
        try:
            shutil.rmtree(temporary_dir)
        except Exception as E:
            nonebot.logger.warning(f"清空临时目录错误，我真是栓Q：{E}")
            continue

    os.makedirs(temporary_dir)
    nonebot.logger.success("删除临时文件目录完成")


@scheduler.scheduled_job("interval", seconds=30)
async def _():
    nonebot.logger.info(
        "-删除临时内容-",
    )
    global something_temporary
    for index_, stuff_component in something_temporary.items():
        if stuff_component["time"] <= 0:  # type: ignore
            if isinstance(stuff_component["stuff"], (str, Path, os.PathLike)):
                try:
                    if os.path.isfile(stuff_component["stuff"]):
                        os.remove(stuff_component["stuff"])
                        nonebot.logger.success(
                            "删除文件：{}".format(stuff_component["stuff"])
                        )
                    elif os.path.isdir(stuff_component["stuff"]):
                        shutil.rmtree(stuff_component["stuff"])
                        nonebot.logger.success(
                            "删除目录：{}".format(stuff_component["stuff"])
                        )
                    else:
                        nonebot.logger.warning(
                            "路径不存在或未知类型：{}".format(stuff_component["stuff"])
                        )
                    del something_temporary[index_]
                except:
                    nonebot.logger.warning(
                        "跳过删除：{}".format(stuff_component["stuff"])
                    )
            else:
                try:
                    nonebot.logger.info(
                        "清理内存：{}".format(stuff_component["stuff"][-1])  # type: ignore
                    )
                    del something_temporary[index_]
                except:
                    nonebot.logger.warning(
                        "无法删除：{}".format(stuff_component["stuff"][-1])  # type: ignore
                    )
        else:
            something_temporary[index_]["time"] -= 1  # type: ignore
    global filesaves
    qqidlist = list(filesaves.keys()).copy()
    save_file = False
    for qqid in qqidlist:
        namelist = list(filesaves[qqid].keys()).copy()
        for name in namelist:
            if name == "totalSize":
                continue
            elif (
                zhDateTime.DateTime.now()
                - zhDateTime.DateTime(*filesaves[qqid][name]["date"])
            ).seconds > cache_limit_data[os.path.splitext(name)[-1]][1]:
                try:
                    os.remove(database_dir / qqid / name)
                except:
                    pass

                filesaves[qqid]["totalSize"] -= filesaves[qqid][name]["size"]
                nonebot.logger.info(
                    "\t删除{}".format(name),
                )
                filesaves[qqid].pop(name)
                save_file = True

        try:
            is_dir_empty = not os.listdir(
                database_dir / qqid,
            )
        except:
            is_dir_empty = True

        if (
            (filesaves[qqid]["totalSize"] <= 0)
            or len(filesaves[qqid].keys()) == 1
            or is_dir_empty
        ):
            try:
                shutil.rmtree(
                    database_dir / qqid,
                )
            except:
                pass
            filesaves.pop(qqid)
            save_file = True
    if save_file:
        nonebot.logger.success("-已删除过期内容-")
        save_filesaves()
    else:
        nonebot.logger.success("-无过期内容需要删除-")


# @nonebot.rule.Rule
# def file_receive_rule(event: GroupMessageEvent):
#     return event.get_type() == "group_upload"

notece_ = nonebot.on_notice()


@notece_.handle()
async def _(
    event: GroupUploadNoticeEvent,
    bot: T_Bot,
):
    # global cache_limit_data
    file_infomation = event.model_dump()["file"]
    file_subtype: str = os.path.splitext(file_infomation["name"])[-1].lower()
    if file_subtype in cache_limit_data.keys():
        if file_infomation["size"] > cache_limit_data[file_subtype][0]:
            await notece_.finish(
                "文件 {} 大小过大，这不是网盘\n单个{}文件不应大于 {} 千字节".format(
                    file_infomation["name"],
                    file_subtype.upper(),
                    cache_limit_data[file_subtype][0] / 1024,
                ),
                at_sender=True,
            )
            return
        elif (usr_id := str(event.user_id)) in filesaves.keys():
            if (
                filesaves[usr_id]["totalSize"] + file_infomation["size"]
                > max_cache_size
            ):
                await notece_.send(
                    "缓存容量已经耗尽，当前你在服务器内的占有为 {} 字节，合 {}/{} 千字节\n而服务器最多支持每个人占有 {} 兆字节（即 {} 字节）".format(
                        filesaves[usr_id]["totalSize"],
                        int(filesaves[usr_id]["totalSize"] / 10.24 + 0.5) / 100,
                        max_cache_size / 1024,
                        max_cache_size / 1048576,
                        max_cache_size,
                    ),
                    at_sender=True,
                )
                await notece_.finish(
                    f"执行指令 清除缓存（clearCache） 以清除在服务器内存储的缓存文件。",
                )
                return
            if file_infomation["name"] in filesaves[usr_id]:
                await notece_.finish(
                    "你的缓存中已经包含了名称为 {} 的文件，不可重复上传。".format(
                        file_infomation["name"]
                    )
                )
                return
        savepath = database_dir / usr_id

        os.makedirs(savepath, exist_ok=True)

        async with aiohttp.ClientSession() as client:
            resp = await client.get(file_infomation["url"], verify_ssl=False)
            (savepath / file_infomation["name"]).open("wb").write(
                await resp.content.read()
            )

        now = zhDateTime.DateTime.now()
        try:
            filesaves[usr_id][file_infomation["name"]] = {
                "date": [
                    now.year,
                    now.month,
                    now.day,
                    now.hour,
                    now.minute,
                ],
                "size": file_infomation["size"],
            }
            filesaves[usr_id]["totalSize"] += file_infomation["size"]
        except:
            filesaves[usr_id] = {
                file_infomation["name"]: {
                    "date": [
                        now.year,
                        now.month,
                        now.day,
                        now.hour,
                        now.minute,
                    ],
                    "size": file_infomation["size"],
                }
            }
            filesaves[usr_id]["totalSize"] = file_infomation["size"]
        save_filesaves()
        await notece_.finish(
            "文件 {} 已经保存，此文件在{:.1f}分内有效。".format(
                file_infomation["name"], cache_limit_data[file_subtype][1] / 60
            ),
            at_sender=True,
        )


on_convert_help = on_alconna(
    command=Alconna("查看帮助"),
    aliases={
        "转换帮助",
        "查看转换帮助",
        "cvt_help",
        "convert_help",
        "cvthlp",
    },
    rule=nonebot.rule.to_me(),
)


@on_convert_help.handle()
async def _(
    event: GroupMessageEvent,
    bot: T_Bot,
):
    await on_clear_cache.finish(
        UniMessage.image(path=(Path(__file__).parent / "convert_helper.png")),
        at_sender=True,
    )
    # await MarkdownMessage.send_md(
    #     (Path(__file__).parent / "convert_helper.md").read_text(encoding="utf-8"),
    #     bot,
    #     event=event,
    # )


on_clear_cache = on_alconna(
    command=Alconna("清除缓存"),
    aliases={
        "clearCache",
        "clearcache",
        "ClearCache",
        "清除文件缓存",
        "清除缓存文件",
        "清空缓存",
    },
)


@on_clear_cache.handle()
async def _(
    event: GroupMessageEvent,
    bot: T_Bot,
):
    if (usr_id := str(event.user_id)) in people_convert_point:
        del people_convert_point[usr_id]

    if usr_id in filesaves.keys():
        shutil.rmtree(database_dir / usr_id)
        genText = (
            "、".join([i if i != "totalSize" else "" for i in filesaves[usr_id].keys()])
            .replace("、、", "、")
            .strip("、")
        )
        del filesaves[usr_id]
        save_filesaves()
        await on_clear_cache.finish(
            UniMessage.text("文件 {} 已经清除。".format(genText)),
            at_sender=True,
        )
    else:
        await on_clear_cache.finish(
            UniMessage.text("服务器内未存有阁下的缓存文件。"),
            at_sender=True,
        )


on_list_cache = on_alconna(
    command=Alconna("查看缓存"),
    aliases={"listCache", "listcache", "ListCache", "查看文件缓存", "查看缓存文件"},
)


@on_list_cache.handle()
async def _(
    event: GroupMessageEvent,
    bot: T_Bot,
):
    if (usr_id := str(event.user_id)) in filesaves.keys():
        genText = (
            "\n".join(
                [
                    (
                        "{}({}千字节): 剩余{}秒".format(
                            i,
                            int(j["size"] / 10.24 + 0.5) / 100,
                            cache_limit_data[os.path.splitext(i)[-1].lower()][1]
                            - (
                                zhDateTime.DateTime.now()
                                - zhDateTime.DateTime(*j["date"])
                            ).seconds,
                        )
                        if i != "totalSize"
                        else ""
                    )
                    for i, j in filesaves[usr_id].items()
                ]
            )
            .replace("\n\n", "\n")
            .strip("\n")
        )
        await on_list_cache.finish(
            UniMessage.text(
                "服务器中保有你的如下文件：\n{}\n共计 {}/{} 字节，合 {}/{} 千字节".format(
                    genText,
                    filesaves[usr_id]["totalSize"],
                    max_cache_size,
                    int(filesaves[usr_id]["totalSize"] / 10.24 + 0.5) / 100,
                    max_cache_size / 1024,
                )
            ),
            at_sender=True,
        )
    else:
        await on_clear_cache.finish(
            UniMessage.text("服务器内未存有阁下的缓存文件。"),
            at_sender=True,
        )


# def convert_midi(
#         midi_file_path: str,
#         play_speed: float = 1,
#         default_tempo: int = Musicreater.mido.midifiles.midifiles.DEFAULT_TEMPO,
#         pitched_note_table: Musicreater.MidiInstrumentTableType = Musicreater.MM_TOUCH_PITCHED_INSTRUMENT_TABLE,
#         percussion_note_table: Musicreater.MidiInstrumentTableType = Musicreater.MM_TOUCH_PERCUSSION_INSTRUMENT_TABLE,
#         old_exe_format: bool = False,
#         min_volume: float = 0.1,
#         vol_processing_func: Musicreater.FittingFunctionType = Musicreater.natural_curve,
#     )

linglun_convert = on_alconna(
    aliases={
        "linglun_convert",
        "音乐转换",
        "midi转换",
        "转换音乐",
        "linglun_music_convert",
    },
    command=Alconna(
        "llmscvt",
        Option("-f|--file", default="all", args=Args["file", str, "all"]),  # ALL
        Option("-emr|--enable-mismatch-error", default=False, action=store_true),
        Option("-ps|--play-speed", default=1.0, args=Args["play-speed", float, 1.0]),
        Option(
            "-dftp|--default-tempo",
            default=Musicreater.mido.midifiles.midifiles.DEFAULT_TEMPO,
            args=Args[
                "default-tempo", int, Musicreater.mido.midifiles.midifiles.DEFAULT_TEMPO
            ],
        ),
        Option(
            "-ptc|--pitched-note-table",
            default="touch",
            args=Args["pitched-note-table", str, "touch"],
        ),
        Option(
            "-pcs|--percussion-note-table",
            default="touch",
            args=Args["percussion-note-table", str, "touch"],
        ),
        Option("-e|--old-execute-format", default=False, action=store_true),
        Option(
            "-mv|--minimal-volume", default=0.1, args=Args["minimal-volume", float, 0.1]
        ),
        Option(
            "-vpf|--volume-processing-function",
            default="natural",
            args=Args["volume-processing-function", str, "natural"],
        ),
        Option("-t|-type", default="all", args=Args["type", str, "all"]),
        Option("-htp|--high-time-precision", default=False, action=store_true),
        # Option("-dpb|--disable-progress-bar", default=False, action=store_true),
        Option(
            "-pgb|--progress-bar",
            default=None,
            args=Args["base_s", str, r"▶ %%N [ %%s/%^s %%% §e__________§r %%t|%^t ]"][
                "to_play_s", str, r"§7="
            ]["played_s", str, r"="],
        ),
        Option(
            "-s|--scoreboard-name",
            default="mscplay",
            args=Args["scoreboard-name", str, "mscplay"],
        ),
        Option("-dsa|--disable-scoreboard-autoreset", default=False, action=store_true),
        Option(
            "-p|--player-selector",
            default="@a",
            args=Args["player-selector", str, "@a"],
        ),
        Option("-l|--height-limit", default=32, args=Args["height-limit", int, 32]),
        Option("-a|--author", default="Eilles", args=Args["author", str, "Eilles"]),
        Option(
            "-fa|--forward-axis", default="z+", args=Args["forward-axis", str, "z+"]
        ),
    ),
    # permission=SUPERUSER,
)


@linglun_convert.handle()
async def _(
    result: Arparma,
    event: GroupMessageEvent | PrivateMessageEvent,
    bot: T_Bot,
):

    nonebot.logger.info(result.options)

    usr_id = event.get_user_id()
    ulang = get_user_lang(usr_id)

    superuser_permission = await SUPERUSER(bot, event)

    if ((qres := query_convert_points(usr_id, "music"))[0] is False) and (
        not superuser_permission
    ):
        await linglun_convert.finish(
            UniMessage.text(
                ulang.get(
                    "convet.not_enough_point",
                    NOW=qres[1],
                    TOTAL=configdict["maxPersonConvert"]["music"],
                )
            ),
            at_sender=True,
        )

    _args: dict = {
        "file": "all",
        "enable-mismatch-error": False,
        "play-speed": 1.0,
        "default-tempo": 500000,
        "pitched-note-table": "touch",
        "percussion-note-table": "touch",
        "old-execute-format": False,
        "minimal-volume": 0.1,
        "volume-processing-function": "natural",
        "type": "all",
        "high-time-precision": False,
        "progress-bar": {
            "base_s": r"▶ %%N [ %%s/%^s %%% §e__________§r %%t|%^t ]",
            "to_play_s": r"§7=",
            "played_s": r"=",
        },
        "scoreboard-name": "mscplay",
        "disable-scoreboard-autoreset": False,
        "player-selector": "@a",
        "height-limit": 32,
        "author": "Eilles",
        "forward-axis": "z+",
    }
    for arg in _args.keys():
        _args[arg] = (
            (
                result.options[arg].args[arg]
                if arg in result.options[arg].args.keys()
                else result.options[arg].args
            )
            if (
                (_vlu := result.options[arg].value) is None
                or isinstance(_vlu, EllipsisType)
            )
            else _vlu
        )
    # await musicreater_convert.finish(
    #     UniMessage.text(json.dumps(_args, indent=4, sort_keys=True, ensure_ascii=False))
    # )
    nonebot.logger.info(_args)

    if ((not superuser_permission) and (usr_id not in filesaves.keys())) or (
        superuser_permission
        and (
            (not len(filesaves))
            or (_args["file"].lower() == "all" and usr_id not in filesaves.keys())
        )
    ):
        await linglun_convert.finish(
            UniMessage.text(ulang.get("convert.no_file", TYPE="midi"))
        )
        return

    # usr_data_path = database_dir / usr_id
    (usr_temp_path := temporary_dir / usr_id).mkdir(exist_ok=True)

    if (_ppnt := _args["pitched-note-table"].lower()) in [
        "touch",
        "classic",
        "dislink",
    ]:
        pitched_notechart = (
            Musicreater.MM_DISLINK_PITCHED_INSTRUMENT_TABLE
            if _ppnt == "dislink"
            else (
                Musicreater.MM_CLASSIC_PITCHED_INSTRUMENT_TABLE
                if _ppnt == "classic"
                else Musicreater.MM_TOUCH_PITCHED_INSTRUMENT_TABLE
            )
        )
    elif (
        _ppnt := get_stored_path(
            usr_id, _args["pitched-note-table"], superuser_permission
        )
    ).exists():
        pitched_notechart = Musicreater.MM_TOUCH_PITCHED_INSTRUMENT_TABLE.copy()
        pitched_notechart.update(json.load(_ppnt.open("r")))
    else:
        await linglun_convert.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="乐音乐器对照表",
                    NAME=_args["pitched-note-table"],
                )
            )
        )
        return

    if (_ppnt := _args["percussion-note-table"].lower()) in [
        "touch",
        "classic",
        "dislink",
    ]:
        percussion_notechart = (
            Musicreater.MM_DISLINK_PERCUSSION_INSTRUMENT_TABLE
            if _ppnt == "dislink"
            else (
                Musicreater.MM_CLASSIC_PERCUSSION_INSTRUMENT_TABLE
                if _ppnt == "classic"
                else Musicreater.MM_TOUCH_PERCUSSION_INSTRUMENT_TABLE
            )
        )
    elif (
        _ppnt := get_stored_path(
            usr_id, _args["percussion-note-table"], superuser_permission
        )
    ).exists():
        percussion_notechart = Musicreater.MM_TOUCH_PERCUSSION_INSTRUMENT_TABLE.copy()
        percussion_notechart.update(json.load(_ppnt.open("r")))
    else:
        await linglun_convert.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="打击乐器对照表",
                    NAME=_args["percussion-note-table"],
                )
            )
        )
        return

    if (_ppnt := _args["volume-processing-function"].lower()) in [
        "natural",
        "straight",
    ]:
        volume_curve = (
            Musicreater.straight_line
            if _ppnt == "straight"
            else Musicreater.natural_curve
        )
    else:
        await linglun_convert.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="音量处理曲线",
                    NAME=_args["volume-processing-function"],
                )
            )
        )
        return

    if (_ppnt := _args["type"].lower()) == "all":
        all_cvt_types = [
            "addon-delay",
            "addon-score",
            "mcstructure-dalay",
            "mcstructure-score",
            "bdx-delay",
            "bdx-score",
            "msq",
        ]
    else:
        all_cvt_types = _ppnt.split("&")

    # 重定向标准输出
    buffer = StringIO()
    sys.stdout = buffer
    sys.stderr = buffer

    def go_chk_point() -> bool:
        res, pnt = query_convert_points(
            usr_id,
            "music",
            random.random() % 0.5 + 0.3,
        )
        if not res:
            buffer.write(ulang.get("convert.break.not_enough_point", NOW=pnt))
        return res

    await linglun_convert.send(
        UniMessage.text(ulang.get("convert.start"))
    )

    try:

        progress_bar_style = (
            Musicreater.ProgressBarStyle(**_args["progress-bar"])
            if _args["progress-bar"]
            else None
        )

        all_files: dict[str, dict[str, dict[str, int | tuple | str | list]]] = {}

        for file_to_convert in (
            filesaves[usr_id].keys()
            if _args["file"].lower() == "all"
            else _args["file"].split("&")
        ):
            if file_to_convert.endswith(".mid") or file_to_convert.endswith(".midi"):
                nonebot.logger.info("载入转换文件：{}".format(file_to_convert))

                to_convert_path = get_stored_path(
                    usr_id, file_to_convert, superuser_permission
                )

                if to_convert_path.is_file():
                    all_files[to_convert_path.name] = {}
                else:
                    continue

                identify_cmp = str(
                    (
                        os.path.splitext(to_convert_path.name)[0].replace(" ", "_"),
                        not _args["enable-mismatch-error"],
                        _args["play-speed"],
                        _args["default-tempo"],
                        str(pitched_notechart),
                        str(percussion_notechart),
                        volume_curve,
                    ).__hash__()
                )

                if identify_cmp in something_temporary.keys():
                    nonebot.logger.info("载入已有缓存。")
                    msct_obj: Musicreater.MidiConvert = read_memory_from_temporary(
                        identify_cmp
                    )
                    msct_obj.redefine_execute_format(_args["old-execute-format"])
                    msct_obj.set_min_volume(_args["minimal-volume"])
                    # msct_obj.set_deviation()
                else:
                    if go_chk_point():
                        msct_obj = Musicreater.MidiConvert.from_midi_file(
                            midi_file_path=str(to_convert_path),
                            mismatch_error_ignorance=not _args["enable-mismatch-error"],
                            play_speed=_args["play-speed"],
                            default_tempo=_args["default-tempo"],
                            pitched_note_table=pitched_notechart,
                            percussion_note_table=percussion_notechart,
                            old_exe_format=_args["old-execute-format"],
                            min_volume=_args["minimal-volume"],
                            vol_processing_func=volume_curve,
                        )
                        add_memory_to_temporary(
                            identify_cmp,
                            msct_obj,
                            "音乐转换类{}".format(msct_obj.music_name),
                            7,
                        )
                    else:
                        buffer.write(
                            "点数不足或出现错误：{}".format(
                                to_convert_path.name,
                            )
                        )
                        continue

                # people_convert_point[usr_id] += 0.5

                if "msq" in all_cvt_types:
                    all_files[file_to_convert]["msq"] = {"MSQ版本": "2-MSQ@"}
                    (usr_temp_path / "{}.msq".format(msct_obj.music_name)).open(
                        "wb"
                    ).write(
                        msct_obj.encode_dump(
                            high_time_precision=_args["high-time-precision"]
                        )
                    )

                if go_chk_point() and "addon-delay" in all_cvt_types:
                    all_files[file_to_convert]["addon-delay"] = dict(
                        zip(
                            ["指令数量", "音乐刻长"],
                            to_addon_pack_in_delay(
                                midi_cvt=msct_obj,
                                dist_path=str(usr_temp_path),
                                progressbar_style=progress_bar_style,
                                player=_args["player-selector"],
                                max_height=_args["height-limit"],
                            ),
                        )
                    )
                    # people_convert_point[usr_id] += 0.5
                    # all_cvt_types.remove("addon-delay")

                if go_chk_point() and "addon-score" in all_cvt_types:
                    all_files[file_to_convert]["addon-score"] = dict(
                        zip(
                            ["指令数量", "音乐刻长"],
                            to_addon_pack_in_score(
                                midi_cvt=msct_obj,
                                dist_path=str(usr_temp_path),
                                progressbar_style=progress_bar_style,
                                scoreboard_name=_args["scoreboard-name"],
                                auto_reset=not _args["disable-scoreboard-autoreset"],
                            ),
                        )
                    )
                    # people_convert_point[usr_id] += 0.5
                    # all_cvt_types.remove("addon-score")

                if go_chk_point() and "mcstructure-dalay" in all_cvt_types:
                    all_files[file_to_convert]["mcstructure-dalay"] = dict(
                        zip(
                            ["结构尺寸", "音乐刻长"],
                            to_mcstructure_file_in_delay(
                                midi_cvt=msct_obj,
                                dist_path=str(usr_temp_path),
                                player=_args["player-selector"],
                                max_height=_args["height-limit"],
                            ),
                        )
                    )
                    # people_convert_point[usr_id] += 0.5
                    # all_cvt_types.remove("mcstructure-dalay")

                if go_chk_point() and "mcstructure-score" in all_cvt_types:
                    all_files[file_to_convert]["mcstructure-score"] = dict(
                        zip(
                            ["结构尺寸", "音乐刻长", "指令数量"],
                            to_mcstructure_file_in_score(
                                midi_cvt=msct_obj,
                                dist_path=str(usr_temp_path),
                                scoreboard_name=_args["scoreboard-name"],
                                auto_reset=not _args["disable-scoreboard-autoreset"],
                                max_height=_args["height-limit"],
                            ),
                        )
                    )
                    # people_convert_point[usr_id] += 0.5
                    # all_cvt_types.remove("mcstructure-score")

                if go_chk_point() and "bdx-delay" in all_cvt_types:
                    all_files[file_to_convert]["bdx-delay"] = dict(
                        zip(
                            [
                                "指令数量",
                                "音乐刻长",
                                "结构尺寸",
                                "终点坐标",
                            ],
                            to_BDX_file_in_delay(
                                midi_cvt=msct_obj,
                                dist_path=str(usr_temp_path),
                                progressbar_style=progress_bar_style,
                                player=_args["player-selector"],
                                author=_args["author"],
                                max_height=_args["height-limit"],
                            ),
                        )
                    )
                    # people_convert_point[usr_id] += 0.5
                    # all_cvt_types.remove("bdx-delay")

                if go_chk_point() and "bdx-score" in all_cvt_types:
                    all_files[file_to_convert]["bdx-score"] = dict(
                        zip(
                            [
                                "指令数量",
                                "音乐刻长",
                                "结构尺寸",
                                "终点坐标",
                            ],
                            to_BDX_file_in_score(
                                midi_cvt=msct_obj,
                                dist_path=str(usr_temp_path),
                                progressbar_style=progress_bar_style,
                                scoreboard_name=_args["scoreboard-name"],
                                auto_reset=not _args["disable-scoreboard-autoreset"],
                                author=_args["author"],
                                max_height=_args["height-limit"],
                            ),
                        )
                    )
                    # people_convert_point[usr_id] += 0.5
                    # all_cvt_types.remove("bdx-score")
            elif file_to_convert != "totalSize":
                nonebot.logger.warning(
                    "文件类型错误：{}".format(file_to_convert),
                )
                buffer.write("文件 {} 已跳过\n".format(file_to_convert))

        if not all_files:
            nonebot.logger.warning(
                "无可供转换的文件",
            )
            await linglun_convert.finish(
                UniMessage(
                    "不是哥/姐/Any们，二氧化碳咱这转不成面包，那是中科院的事。\n*所指向之文件皆不存在"
                )
            )

    except Exception as e:
        nonebot.logger.error("转换存在错误：{}".format(e))
        buffer.write(
            "[ERROR] {}\n".format(e).replace(str(Path(__file__).parent.resolve()), "[]")
        )

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    Musicreater.plugin.archive.compress_zipfile(
        usr_temp_path,
        fp := str(
            (
                temporary_dir
                / (fn := "msctr[{}]-{}.zip".format(hanzi_timeid(), usr_id))
            ).resolve()
        ),
    )

    shutil.rmtree(usr_temp_path)

    # await linglun_convert.send(UniMessage.file(name=fn, path=fp))

    if isinstance(event, GroupMessageEvent) or isinstance(
        event, GroupUploadNoticeEvent
    ):
        await bot.call_api(
            "upload_group_file", group_id=event.group_id, name=fn, file=fp
        )
        # await linglun_convert.send(
        #     UniMessage.text("文件已上传群文件，请在群文件查看。")
        # )
        # await linglun_convert.send(UniMessage.file(res_id,path=fp,name=fn))
    else:
        await bot.call_api(
            "upload_private_file", user_id=event.user_id, name=fn, file=fp
        )

    img_bytes = await md_to_pic(
        "##{}\n\n```\n{}\n```".format(
            MarkdownMessage.escape("日志信息："),
            buffer.getvalue().replace("\\", "/"),
        ),
    )
    await UniMessage.send(UniMessage.image(raw=img_bytes))

    # nonebot.logger.info(buffer.getvalue())
    img_bytes = await md_to_pic(
        "## 转换结果\n\n"
        + ("\n\n\n").join(
            [
                "###{}\n\n{}".format(
                    fn,
                    "\n\n".join(
                        [
                            "- {}\n\t{}".format(
                                tn,
                                "\n\t".join(
                                    ["- {} : {}".format(i, j) for i, j in rps.items()]
                                ),
                            )
                            for tn, rps in res.items()
                        ]
                    ),
                )
                for fn, res in all_files.items()
            ]
        )
        + "\n\n### 言·论 \n\n **{}**".format(random_yanlun_text()),
    )
    await UniMessage.send(UniMessage.image(raw=img_bytes))

    add_file_to_delete(fp, 1)

    await linglun_convert.finish(
        UniMessage.text(
            "转换结束，当前剩余转换点数：⌊p⌋≈{:.2f}|{}".format(
                query_convert_points(
                    usr_id,
                    "music",
                    0,
                )[1],
                configdict["maxPersonConvert"]["music"],
            )
        ),
        at_sender=True,
    )


reset_point = on_alconna(
    command=Alconna(
        "设置点数",
        Option(
            "-p|--people",
            default="Now",
            args=Args["people", str, "Now"],
        ),
        Option(
            "-v|--value",
            default=0,
            args=Args["value", float | int, 0],
        ),
        Option(
            "-i|--item",
            default="music",
            args=Args["item", str, "music"],
        ),
    ),
    aliases={
        "增加转换点数",
        "add_convert_point",
        "increase_cvt_pnt",
        "addcp",
        "icrcp",
        "icr_convert_point",
        "重设并增加转换点数",
    },
    permission=SUPERUSER,
    rule=nonebot.rule.to_me(),
)


@reset_point.handle()
async def _(
    result: Arparma,
    event: GroupMessageEvent | PrivateMessageEvent,
    bot: T_Bot,
):
    # event.user_id
    to_change = (
        (
            str(event.user_id)
            if result.options["people"].args["people"] == "Now"
            else result.options["people"].args["people"]
        )
        if result.options["people"].args
        else str(event.user_id)
    )
    cd_value = (
        result.options["value"].args["value"] if result.options["value"].args else 0
    )
    v_item = (
        result.options["item"].args["item"] if result.options["item"].args else "music"
    )

    if v_item not in configdict["maxPersonConvert"]:
        await linglun_convert.finish(
            UniMessage.text(
                "错误！没有名为 {} 的项目。".format(v_item),
            ),
            at_sender=True,
        )

    await linglun_convert.finish(
        UniMessage.text(
            "重置转换状况并修改点数成功！当前{}的{}点数为：⌊p⌋≈{:.2f}|{}".format(
                to_change,
                v_item,
                query_convert_points(
                    to_change,
                    v_item,
                    -cd_value,
                )[1],
                configdict["maxPersonConvert"][v_item],
            )
        ),
        # at_sender=True,
    )


execute_cmd_convert_ablity = on_alconna(
    command=Alconna("指令自动更新"),
    aliases={
        "指令更新自动",
        "自动指令更新",
        "指令更新",
    },
)


@execute_cmd_convert_ablity.handle()
async def _(
    event: T_MessageEvent,
    bot: T_Bot,
):
    ulang = get_user_lang(usrid := str(event_utils.get_user_id(event)))
    global enable_auto_exe_translate
    enable_auto_exe_translate[usrid] = not enable_auto_exe_translate.get(usrid, True)
    await execute_cmd_convert_ablity.finish(
        UniMessage.text(
            ulang.get(
                "upexecute.enable"
                if enable_auto_exe_translate[usrid]
                else "upexecute.disable"
            )
        )
    )


execute_cmd_convert = nonebot.on_startswith(
    "execute",
)


@execute_cmd_convert.handle()
async def _(
    event: T_MessageEvent,
    bot: T_Bot,
):
    global enable_auto_exe_translate
    if not enable_auto_exe_translate.get(
        usrid := str(event_utils.get_user_id(event)), True
    ):
        execute_cmd_convert.destroy()
        return
    ulang = get_user_lang(usrid)
    if (
        result_execmd := auto_translate(event.get_plaintext())
    ) == event.get_plaintext():
        await execute_cmd_convert.finish(ulang.get("upexecute.same"))
    else:
        await execute_cmd_convert.finish(result_execmd)


# test_exec = nonebot.on_command(
#     "test-exec",
#     rule=to_me(),
#     permission=SUPERUSER,
# )


# @test_exec.handle()
# async def _(args: Annotated[nonebot.adapters.Message, CommandArg()]):
#     await test_exec.finish(exec(args.extract_plain_text()))
