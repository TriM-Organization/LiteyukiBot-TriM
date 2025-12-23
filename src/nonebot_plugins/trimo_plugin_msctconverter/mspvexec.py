import os
import sys
import json
import shutil
import random

from io import StringIO
from pathlib import Path
from types import EllipsisType

# import nonebot.rule

import mido
import nonebot
import soundfile
import Musicreater
import Musicreater.plugin
import nonebot.adapters.onebot.v11.exception

from .MusicPreview.main import PreviewMusic

from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    PrivateMessageEvent,
    GroupUploadNoticeEvent,
)
from nonebot_plugin_alconna import (
    Alconna,
    # AlconnaQuery,
    Args,
    # Image,
    Option,
    # Query,
    # Text,
    UniMessage,
    on_alconna,
    # Voice,
    Arparma,
    Args,
    store_true,
)

from src.utils.base.ly_typing import T_Bot, T_MessageEvent
from src.utils.message.message import MarkdownMessage
from src.utils.message.html_tool import md_to_pic

from .msctexec import (
    something_temporary,
    query_convert_points,
    filesaves,
    configdict,
    temporary_dir,
    add_file_to_delete,
    add_memory_to_temporary,
    read_memory_from_temporary,
    get_stored_path,
    get_user_lang,
)
from .utils import hanzi_timeid

mspv_sync = on_alconna(
    Alconna(
        "音乐合成",
        Option("-n|-f|--file-name", default="all", args=Args["file-name", str, "all"]),
        Option("-m|--mode", default=0, args=Args["mode", int, 0]),
        Option(
            "-g|--get-value-method", default=1, args=Args["get-value-method", int, 1]
        ),
        Option("-o|--output-file", default=False, action=store_true),
        Option("-emr|--enable-mismatch-error", default=False, action=store_true),
        Option("-ps|--play-speed", default=1.0, args=Args["play-speed", float, 1.0]),
        Option(
            "-dftp|--default-tempo",
            default=mido.midifiles.midifiles.DEFAULT_TEMPO,
            args=Args["default-tempo", int, mido.midifiles.midifiles.DEFAULT_TEMPO],
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
        Option(
            "-vpf|--volume-processing-function",
            default="natural",
            args=Args["volume-processing-function", str, "natural"],
        ),
        Option("--debug", default=False, action=store_true),
    ),
    aliases={
        "midi合成",
        "音乐预览",
        "mscprv",
        "music_preview",
        "预览音乐效果",
        "预览音乐",
    },
    # rule=nonebot.rule.to_me(),
    # use_cmd_start=True,
    # block=True,
    # priority=13,
)


@mspv_sync.handle()
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
        await mspv_sync.finish(
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
        "file-name": "all",
        "output-file": False,
        "mode": 0,
        "get-value-method": 1,
        "enable-mismatch-error": False,
        "play-speed": 1.0,
        "default-tempo": 500000,
        "pitched-note-table": "touch",
        "percussion-note-table": "touch",
        "volume-processing-function": "natural",
        "debug": False,
    }
    for arg in _args.keys():
        _args[arg] = (
            (
                result.options[arg].args[arg]
                if arg in result.options[arg].args.keys()
                else result.options[arg].args
            )
            if ((_vlu := result.options[arg].value) is None)
            or isinstance(_vlu, EllipsisType)
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
            or (_args["file-name"].lower() == "all" and usr_id not in filesaves.keys())
        )
    ):
        await mspv_sync.finish(
            UniMessage.text(ulang.get("convert.no_file", TYPE="midi"))
        )
        return

    if _args["mode"] not in (0, 1, 2, 3, 4):
        await mspv_sync.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="模式",
                    NAME=_args["mode"],
                )
            )
        )

    if _args["get-value-method"] not in (0, 1):
        await mspv_sync.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="取值法",
                    NAME=_args["get-value-method"],
                )
            )
        )

    # usr_data_path = database_dir / usr_id
    (usr_temp_path := temporary_dir / usr_id).mkdir(exist_ok=True)

    if (_ppnt := _args["pitched-note-table"].lower()) in (
        "touch",
        "classic",
        "dislink",
        "nbs",
    ):
        pitched_notechart = (
            Musicreater.MM_DISLINK_PITCHED_INSTRUMENT_TABLE
            if _ppnt == "dislink"
            else (
                Musicreater.MM_CLASSIC_PITCHED_INSTRUMENT_TABLE
                if _ppnt == "classic"
                else (
                    Musicreater.MM_NBS_PITCHED_INSTRUMENT_TABLE
                    if _ppnt == "nbs"
                    else Musicreater.MM_TOUCH_PITCHED_INSTRUMENT_TABLE
                )
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
        await mspv_sync.finish(
            ulang.get(
                "convert.something_not_exist",
                WHAT="乐音乐器对照表",
                NAME=_args["pitched-note-table"],
            )
        )
        return

    if (_ppnt := _args["percussion-note-table"].lower()) in (
        "touch",
        "classic",
        "dislink",
        "nbs",
    ):
        percussion_notechart = (
            Musicreater.MM_DISLINK_PERCUSSION_INSTRUMENT_TABLE
            if _ppnt == "dislink"
            else (
                Musicreater.MM_CLASSIC_PERCUSSION_INSTRUMENT_TABLE
                if _ppnt == "classic"
                else (
                    Musicreater.MM_NBS_PERCUSSION_INSTRUMENT_TABLE
                    if _ppnt == "nbs"
                    else Musicreater.MM_TOUCH_PERCUSSION_INSTRUMENT_TABLE
                )
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
        await mspv_sync.finish(
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
            Musicreater.velocity_2_distance_straight
            if _ppnt == "straight"
            else Musicreater.velocity_2_distance_natural
        )
    else:
        await mspv_sync.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="音量处理曲线",
                    NAME=_args["volume-processing-function"],
                )
            )
        )
        return

    # 重定向标准输出
    buffer = StringIO()
    sys.stdout = buffer
    sys.stderr = buffer

    def go_chk_point():
        res, pnt = query_convert_points(
            usr_id,
            "music",
            random.random() % 1.6 + 1.3,
        )
        if not res:
            buffer.write(ulang.get("convert.break.not_enough_point", NOW=pnt))
        return res

    await mspv_sync.send(UniMessage.text(ulang.get("convert.start")))

    try:

        all_files = []

        for file_to_convert in (
            filesaves[usr_id].keys()
            if _args["file-name"].lower() == "all"
            else _args["file-name"].split("&")
        ):
            if file_to_convert.endswith(".mid") or file_to_convert.endswith(".midi"):
                nonebot.logger.info("载入待合成文件：{}".format(file_to_convert))
                # print("1")
                # await mspv_sync.finish("处理中")

                to_convert_path = get_stored_path(
                    usr_id, file_to_convert, superuser_permission
                )
                if to_convert_path.is_file():
                    all_files.append(to_convert_path.name)
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
                else:

                    if go_chk_point():
                        msct_obj = Musicreater.MidiConvert.from_midi_file(
                            midi_file_path=str(to_convert_path),
                            mismatch_error_ignorance=not _args["enable-mismatch-error"],
                            play_speed=_args["play-speed"],
                            default_tempo=_args["default-tempo"],
                            pitched_note_table=pitched_notechart,
                            percussion_note_table=percussion_notechart,
                            vol_processing_func=volume_curve,
                            midi_charset="latin1",
                        )
                        add_memory_to_temporary(
                            identify_cmp,
                            msct_obj,
                            "音乐转换类{}".format(msct_obj.music_name),
                            7,
                        )
                    else:
                        buffer.write(
                            "点数不足或出现错误：\n{}".format(
                                to_convert_path.name,
                            )
                        )
                        continue

                music_temp = PreviewMusic(
                    msct_obj,
                    mode=_args["mode"],
                    gvm=_args["get-value-method"],
                    default_channel_num=1,
                    overlay_channels=1,
                    out_sr=44100,
                )
                soundfile.write(
                    fp := (
                        usr_temp_path
                        / "[MP0.2.0]{}-M{}.wav".format(
                            msct_obj.music_name, _args["mode"]
                        )
                    ),
                    music_temp.to_wav(),
                    samplerate=music_temp.out_sr,
                    format="wav",
                )
                await mspv_sync.send(UniMessage.text("曲目 {}".format(file_to_convert)))

                fp.open("ab").write(b"DM-MPvR0.2.0")

                await mspv_sync.send(
                    UniMessage.voice(
                        path=fp,
                        name="[MP0.2.0]{}-M{}.wav".format(
                            msct_obj.music_name, _args["mode"]
                        ),
                    )
                )

            elif file_to_convert != "totalSize":
                nonebot.logger.warning(
                    "文件类型错误：{}".format(file_to_convert),
                )
                buffer.write("文件 {} 已跳过\n".format(file_to_convert))

        if not all_files:
            nonebot.logger.warning(
                "无可供读入的文件",
            )
            await mspv_sync.finish(
                UniMessage(
                    "我服了老弟，这机器人也不能给路易十六理发啊。\n*所指向之文件皆不存在"
                )
            )

    except Exception as e:
        nonebot.logger.error("合成存在错误：{}".format(e))
        buffer.write(
            "[ERROR] {}\n".format(e).replace(str(Path(__file__).parent.resolve()), "[]")
        )
        if _args["debug"]:
            raise e

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    if _args["output-file"]:
        Musicreater.plugin.archive.compress_zipfile(
            usr_temp_path,
            fp := str(
                temporary_dir
                / (fn := "mprwav[{}]{}.zip".format(hanzi_timeid(), usr_id))
            ),
        )

        try:
            if isinstance(event, GroupMessageEvent) or isinstance(
                event, GroupUploadNoticeEvent
            ):
                await bot.call_api(
                    "upload_group_file", group_id=event.group_id, name=fn, file=fp
                )
                # await mspv_sync.send(
                #     UniMessage.text("文件已上传群文件，请在群文件查看。")
                # )
            else:
                await bot.call_api(
                    "upload_private_file", user_id=event.user_id, name=fn, file=fp
                )
        except nonebot.adapters.onebot.v11.exception.NetworkError as E:
            buffer.write("文件上传发生网络错误：\n{}".format(E))

        add_file_to_delete(fp, 1)

    if buffer.getvalue().strip():
        img_bytes = await md_to_pic(
            "##{}\n\n```\n{}\n```".format(
                MarkdownMessage.escape("日志信息："),
                buffer.getvalue().replace("\\", "/"),
            ),
        )
        await UniMessage.send(UniMessage.image(raw=img_bytes))

    # nonebot.logger.info(buffer.getvalue())

    shutil.rmtree(usr_temp_path)

    await mspv_sync.finish(
        UniMessage.text(
            "成功转换：{}\n当前剩余转换点数：⌊p⌋≈{:.2f}|{}".format(
                "、".join(all_files),
                query_convert_points(usr_id, "music", 0)[1],
                configdict["maxPersonConvert"]["music"],
            )
        ),
        at_sender=True,
    )
