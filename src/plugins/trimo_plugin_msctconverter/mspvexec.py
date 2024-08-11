import os
import sys
import json
import shutil
import random

from io import StringIO

# from pathlib import Path

# import nonebot.rule

import nonebot
import soundfile
import zhDateTime
import Musicreater
import Musicreater.plugin
import nonebot.adapters.onebot.v11.exception

from .MusicPreview.main import PreviewMusic

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

from .msctexec import (
    # people_convert_point,
    query_convert_points,
    filesaves,
    configdict,
    database_dir,
    temporary_dir,
    file_to_delete,
)
from .utils import utime_hanzify

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
        Option(
            "-vpf|--volume-processing-function",
            default="natural",
            args=Args["volume-processing-function", str, "natural"],
        ),
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
    # print("E:\\Work2024\\test-midi\\" + name.result)

    nonebot.logger.info(result.options)

    usr_id = str(event.user_id)

    if (qres := query_convert_points(usr_id, "music"))[0] is False:
        await mspv_sync.finish(
            UniMessage.text(
                "转换点数不足，当前剩余：⌊p⌋≈{:.2f}|{}".format(
                    qres[1],
                    configdict["maxPersonConvert"]["music"],
                )
            ),
            at_sender=True,
        )

    if usr_id not in filesaves.keys():
        await mspv_sync.finish(
            UniMessage.text("服务器内未存入你的任何文件，请先使用上传midi文件吧")
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

    if _args["mode"] not in [0, 1, 2, 3, 4]:
        await mspv_sync.finish(
            UniMessage.text("模式 {} 不存在，请详阅文档。".format(_args["mode"]))
        )

    if _args["get-value-method"] not in [
        0,
        1,
    ]:
        await mspv_sync.finish(
            UniMessage.text(
                "取值法 {} 不存在，请详阅文档。".format(_args["get-value-method"])
            )
        )

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
        await mspv_sync.finish(
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
        await mspv_sync.finish(
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
        await mspv_sync.finish(
            UniMessage.text(
                "音量处理曲线 {} 不存在".format(_args["volume-processing-function"])
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
        if res is False:
            buffer.write("中途退出，转换点不足：{}\n".format(pnt))
            return False
        else:
            return True

    await mspv_sync.send(UniMessage.text("转换开始……"))

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

                if isinstance(
                    msct_obj := query_convert_points(usr_id, "music", 0)[0], tuple
                ) and (
                    isinstance(msct_obj[0], Musicreater.MidiConvert)
                    and (
                        msct_obj[1]
                        == (
                            not _args["enable-mismatch-error"],
                            _args["play-speed"],
                            _args["default-tempo"],
                            pitched_notechart,
                            percussion_notechart,
                            volume_curve,
                        )
                    )
                    and (
                        msct_obj[0].music_name
                        == os.path.splitext(
                            os.path.basename(usr_data_path / file_to_convert)
                        )[0].replace(" ", "_")
                    )
                ):
                    nonebot.logger.info("载入已有缓存。")
                    msct_obj = msct_obj[0]
                else:

                    if go_chk_point():
                        msct_obj = Musicreater.MidiConvert.from_midi_file(
                            midi_file_path=usr_data_path / file_to_convert,
                            mismatch_error_ignorance=not _args["enable-mismatch-error"],
                            play_speed=_args["play-speed"],
                            default_tempo=_args["default-tempo"],
                            pitched_note_table=pitched_notechart,
                            percussion_note_table=percussion_notechart,
                            vol_processing_func=volume_curve,
                        )
                        query_convert_points(
                            usr_id,
                            "music",
                            0,
                            (
                                msct_obj,
                                (
                                    not _args["enable-mismatch-error"],
                                    _args["play-speed"],
                                    _args["default-tempo"],
                                    pitched_notechart,
                                    percussion_notechart,
                                    volume_curve,
                                ),
                            ),
                        )
                    else:
                        buffer.write(
                            "点数不足或出现错误：\n{}".format(
                                _args,
                            )
                        )
                        break

                all_files.append(file_to_convert)

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
                "无可供转换的文件",
            )
            await mspv_sync.finish(
                UniMessage("我服了老弟，这机器人也不能给路易十六理发啊。")
            )

    except Exception as e:
        nonebot.logger.error("合成存在错误：{}".format(e))
        buffer.write(
            "[ERROR] {}\n".format(e).replace(
                "C:\\Users\\Administrator\\Desktop\\RyBot\\", "[]"
            )
        )

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    if _args["output-file"]:
        Musicreater.plugin.archive.compress_zipfile(
            usr_temp_path,
            fp := str(
                temporary_dir
                / (
                    fn := "mprwav[{}]{}.zip".format(
                        utime_hanzify(zhDateTime.DateTime.now().to_lunar()), usr_id
                    )
                )
            ),
        )

        try:
            if isinstance(event, GroupMessageEvent) or isinstance(
                event, GroupUploadNoticeEvent
            ):
                await bot.call_api(
                    "upload_group_file", group_id=event.group_id, name=fn, file=fp
                )
                await mspv_sync.send(UniMessage.text("文件已上传群文件，请在群文件查看。"))
            else:
                await bot.call_api(
                    "upload_private_file", user_id=event.user_id, name=fn, file=fp
                )
        except nonebot.adapters.onebot.v11.exception.NetworkError as E:
            buffer.write("文件上传发生网络错误：\n{}".format(E))

        global file_to_delete
        file_to_delete.append(fp)

    await MarkdownMessage.send_md(
        "##{}\n\n```\n{}\n```".format(
            MarkdownMessage.escape("日志信息："),
            buffer.getvalue().replace("\\", "/"),
        ),
        bot,
        event=event,
    )

    # nonebot.logger.info(buffer.getvalue())

    shutil.rmtree(usr_temp_path)

    await mspv_sync.finish(
        UniMessage.text(
            "成功转换：{}\n当前剩余转换点数：⌊p⌋≈{:.2f}|{}".format(
                "、".join(all_files),
                query_convert_points(usr_id, "music", 0, None)[1],
                configdict["maxPersonConvert"]["music"],
            )
        ),
        at_sender=True,
    )
