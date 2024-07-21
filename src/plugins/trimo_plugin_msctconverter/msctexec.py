import os
import sys
import time
import json

# import uuid
import shutil
import requests
from io import StringIO
from pathlib import Path
from typing import Annotated, Any

# from nonebot import require

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

from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.event import (
    GroupUploadNoticeEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from src.utils.base.ly_typing import T_Bot, T_MessageEvent

from src.utils import event as event_utils
from src.utils.base.language import get_user_lang
from src.utils.base.config import get_config
from src.utils.message.message import MarkdownMessage

from .execute_auto_translator import auto_translate  # type: ignore


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
            "music": 20,
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

people_convert_times = {}


# 每天1点更新
@scheduler.scheduled_job("cron", hour=4)
async def every_day_update():
    # ulang = Language(get_default_lang_code(), "zh-WY")
    global people_convert_times
    people_convert_times = {}
    nonebot.logger.success("已重置每日转换次数")


@nonebot.get_driver().on_startup
async def _():
    nonebot.logger.info("正在删除临时文件目录")
    while temporary_dir.exists():
        time.sleep(1)
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
        "-删除文件检测-",
    )
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
        nonebot.logger.success("-已删除过期文件-")
        save_filesaves()
    else:
        nonebot.logger.success("-无过期文件需要删除-")


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

        (savepath / file_infomation["name"]).open("wb").write(
            requests.get(
                file_infomation["url"],
                verify=False,
            ).content
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
    if (usr_id := str(event.user_id)) in filesaves.keys():
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

    usr_id = str(event.user_id)

    if usr_id not in people_convert_times.keys():
        people_convert_times[usr_id] = 0
    else:
        if people_convert_times[usr_id] > configdict["maxPersonConvert"]["music"]:
            await linglun_convert.finish(
                UniMessage.text(
                    "你今天音乐转换点数超限： {}/{}".format(
                        people_convert_times[usr_id],
                        configdict["maxPersonConvert"]["music"],
                    )
                ),
                at_sender=True,
            )

    if usr_id not in filesaves.keys():
        await linglun_convert.finish(
            UniMessage.text("服务器内未存入你的任何文件，请先使用上传midi文件吧")
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
            if (_vlu := result.options[arg].value) is None
            else _vlu
        )
    # await musicreater_convert.finish(
    #     UniMessage.text(json.dumps(_args, indent=4, sort_keys=True, ensure_ascii=False))
    # )
    nonebot.logger.info(_args)

    usr_data_path = database_dir / usr_id
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
    elif (_ppnt := (usr_data_path / _args["pitched-note-table"])).exists():
        pitched_notechart = Musicreater.MM_TOUCH_PITCHED_INSTRUMENT_TABLE.copy()
        pitched_notechart.update(json.load(_ppnt.open("r")))
    else:
        await linglun_convert.finish(
            UniMessage.text("乐器对照表 {} 不存在".format(_args["pitched-note-table"]))
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
    elif (_ppnt := (usr_data_path / _args["percussion-note-table"])).exists():
        percussion_notechart = Musicreater.MM_TOUCH_PERCUSSION_INSTRUMENT_TABLE.copy()
        percussion_notechart.update(json.load(_ppnt.open("r")))
    else:
        await linglun_convert.finish(
            UniMessage.text(
                "乐器对照表 {} 不存在".format(_args["percussion-note-table"])
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
                "音量处理曲线 {} 不存在".format(_args["volume-processing-function"])
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
                all_files[file_to_convert] = {}
                msct_obj = Musicreater.MidiConvert.from_midi_file(
                    midi_file_path=usr_data_path / file_to_convert,
                    mismatch_error_ignorance=not _args["enable-mismatch-error"],
                    play_speed=_args["play-speed"],
                    default_tempo=_args["default-tempo"],
                    pitched_note_table=pitched_notechart,
                    percussion_note_table=percussion_notechart,
                    old_exe_format=_args["old-execute-format"],
                    min_volume=_args["minimal-volume"],
                    vol_processing_func=volume_curve,
                )

                people_convert_times[usr_id] += 0.5

                if "msq" in all_cvt_types:
                    all_files[file_to_convert]["msq"] = {"MSQ版本": "2-MSQ@"}
                    (usr_temp_path / "{}.msq".format(msct_obj.music_name)).open(
                        "wb"
                    ).write(
                        msct_obj.encode_dump(
                            high_time_precision=_args["high-time-precision"]
                        )
                    )

                if "addon-delay" in all_cvt_types:
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
                    people_convert_times[usr_id] += 0.5
                    # all_cvt_types.remove("addon-delay")

                if "addon-score" in all_cvt_types:
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
                    people_convert_times[usr_id] += 0.5
                    # all_cvt_types.remove("addon-score")

                if "mcstructure-dalay" in all_cvt_types:
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
                    people_convert_times[usr_id] += 0.5
                    # all_cvt_types.remove("mcstructure-dalay")

                if "mcstructure-score" in all_cvt_types:
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
                    people_convert_times[usr_id] += 0.5
                    # all_cvt_types.remove("mcstructure-score")

                if "bdx-delay" in all_cvt_types:
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
                    people_convert_times[usr_id] += 0.5
                    # all_cvt_types.remove("bdx-delay")

                if "bdx-score" in all_cvt_types:
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
                    people_convert_times[usr_id] += 0.5
                    # all_cvt_types.remove("bdx-score")
            elif file_to_convert != "totalSize":
                nonebot.logger.warning(
                    "文件类型错误：{}".format(file_to_convert),
                )
                buffer.write("文件 {} 已跳过\n".format(file_to_convert))

            if people_convert_times[usr_id] > configdict["maxPersonConvert"]["music"]:
                buffer.write("中途退出：转换点不足\n")
                await linglun_convert.send(
                    UniMessage.text(
                        "今日音乐转换点数超限： {}/{}".format(
                            people_convert_times[usr_id],
                            configdict["maxPersonConvert"]["music"],
                        )
                    ),
                    at_sender=True,
                )
                break

        if not all_files:
            nonebot.logger.warning(
                "无可供转换的文件",
            )
            await linglun_convert.finish(
                UniMessage("不是哥们，空气咱这转不成面包，那是中科院的事。")
            )

    except Exception as e:
        nonebot.logger.error("转换存在错误：{}".format(e))
        buffer.write("[ERROR] {}\n".format(e))

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    Musicreater.plugin.archive.compress_zipfile(
        usr_temp_path,
        fp := str(temporary_dir / (fn := "result-{}.zip".format(usr_id))),
    )

    shutil.rmtree(usr_temp_path)

    if isinstance(event, GroupMessageEvent) or isinstance(
        event, GroupUploadNoticeEvent
    ):
        await bot.call_api(
            "upload_group_file", group_id=event.group_id, name=fn, file=fp
        )
    else:
        await bot.call_api(
            "upload_private_file", user_id=event.user_id, name=fn, file=fp
        )

    await MarkdownMessage.send_md(
        "##{}\n\n```\n{}\n```".format(
            MarkdownMessage.escape("日志信息："),
            buffer.getvalue().replace("\\", "/"),
        ),
        bot,
        event=event,
    )

    # nonebot.logger.info(buffer.getvalue())

    await MarkdownMessage.send_md(
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
        ),
        bot,
        event=event,
    )

    os.remove(fp)

    await linglun_convert.finish(
        UniMessage.text(
            "转换结束，当前所用转换点数： {}/{}".format(
                people_convert_times[usr_id], configdict["maxPersonConvert"]["music"]
            )
        ),
        at_sender=True,
    )

reset_point = on_alconna(
    command=Alconna("设置点数"),
    aliases={
        "设置转换点数",
        "set_convert_point",
        "reset_cvt_pnt",
        "setcp",
        "set_convert_point",
        "重设转换点数",
    },
    permission=SUPERUSER,
    rule=nonebot.rule.to_me(),
)


@reset_point.handle()
async def _(
    event: T_MessageEvent,
    bot: T_Bot,
):
    pass


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
