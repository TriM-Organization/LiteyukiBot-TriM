import os
import sys
import random
import brotli
import shutil

from io import StringIO
from pathlib import Path

import nonebot
import zhDateTime
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.event import (
    GroupUploadNoticeEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
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

from Musicreater.plugin.bdx import (
    BDX_MOVE_KEY,
    bdx_move,
    form_command_block_in_BDX_bytes,
    x,
    y,
    z,
)
from Musicreater.plugin.archive import compress_zipfile

from src.utils.io import read_file
from src.utils.base.language import get_user_lang
from src.utils.base.ly_typing import T_Bot, T_MessageEvent
from src.utils.message.html_tool import md_to_pic
from src.utils.message.message import MarkdownMessage


from .utils import hanzi_timeid
from .msctexec import (
    # something_temporary,
    query_convert_points,
    filesaves,
    save_filesaves,
    configdict,
    temporary_dir,
    add_file_to_delete,
    # add_memory_to_temporary,
    # read_memory_from_temporary,
    get_stored_path,
)

from ..liteyuki_status.status import random_yanlun_text


FACE_VALUE = {
    x: {
        True: 5,
        False: 4,
    },
    y: {
        True: 1,
        False: 0,
    },
    z: {
        True: 3,
        False: 2,
    },
}


def switch_xz(axis: str):
    return z if axis == x else x


def go_forward(forward: bool):
    return 1 if forward else -1


def command_to_a_single_chain_in_BDX_bytes(
    commands: list[tuple[str, bool, str]],
    axis: str,
    forward: bool,
    limit: int = 128,
):
    _bytes = b""
    nowf = True
    nowgo = 0
    for cmd, condition, note in commands:
        is_point = ((nowgo != 0) and (not nowf)) or (nowf and (nowgo != (limit - 1)))
        _bytes += form_command_block_in_BDX_bytes(
            cmd,
            (
                FACE_VALUE[axis][not forward ^ nowf]
                if is_point
                else FACE_VALUE[switch_xz(axis)][True]
            ),
            impluse=2,
            condition=condition,
            needRedstone=False,
            tickDelay=0,
            customName=note,
            executeOnFirstTick=False,
            trackOutput=True,
        )
        nowgo += go_forward(nowf)

        if ((nowgo >= limit) and nowf) or ((nowgo < 0) and (not nowf)):
            nowgo -= go_forward(nowf)

            nowf = not nowf

            _bytes += bdx_move(switch_xz(axis), 1)

        else:
            _bytes += bdx_move(axis, go_forward(not forward ^ nowf))

    # _bytes += move(axis, goahead(forward ^ nowf)*nowgo)
    _bytes += bdx_move(axis, -1 * nowgo)

    return _bytes


def command_to_multiline_BDX_structure_file(
    funcList: list[list[tuple[str, bool, str]]],
    axis_: str,
    forward_: bool,
    limit_: int = 128,
    author: str = "Eilles",
    outfile: str = "./test.bdx",
) -> tuple[bool, int, tuple[int, int, int]]:
    """
    Parameters
    ----------
    funcList: list
        指令集列表： 指令系统[  指令集[  单个指令( str指令, bool条件性 ),  ],  ]
    axis_: str
        坐标增值方向，只能是小写的 `x`,`y`,`z`
    forward_: bool
        是否沿着坐标轴的正方向
    limit_: int
        在延展方向上的长度限制
    author: str
        作者名称
    outfile: str
        输出文件

    Returns
    -------
        成功与否，指令总长度，指令结构总大小
    """

    with open(os.path.abspath(outfile), "w+", encoding="utf-8") as f:
        f.write("BD@")

    _bytes = (
        b"BDX\x00"
        + author.encode("utf-8")
        + b" with TrimOrg: BDX Generator\x00\x01command_block\x00"
    )
    totalSize = {x: 0, y: 1, z: 0}
    totalLen = 0

    # 非链延展方向，即系统延展方向
    antiaxis = switch_xz(axis_)

    while funcList:
        func = funcList.pop(0)

        nowlen = len(func)

        totalLen += nowlen

        # 走一条链的指令方块，会自动复位
        _bytes += command_to_a_single_chain_in_BDX_bytes(func, axis_, forward_, limit_)

        # 不是最后一组
        if funcList:
            # 计算系统延展方向的长度
            totalSize[antiaxis] += 2 + nowlen // limit_

            if totalSize[antiaxis] + 2 <= limit_:
                # 没到头，那就 向前走两步？
                _bytes += bdx_move(antiaxis, 2)
            else:
                # 到头了，那就退回去？
                _bytes += bdx_move(y, 2)
                _bytes += bdx_move(antiaxis, -totalSize[antiaxis])

            # _bytes += move(axis_, -len(func))

        else:
            totalSize[antiaxis] += 1 + nowlen // limit_

        # 计算链延展方向的长度
        totalSize[axis_] = min(max(totalSize[axis_], nowlen), limit_)

    with open(
        os.path.abspath(outfile),
        "ab+",
    ) as f:
        f.write(brotli.compress(_bytes + b"XE"))

    return (True, totalLen, (totalSize[x], totalSize[y], totalSize[z]))


async def read_file_into_command_lines(
    file_: Path,
) -> list[list[tuple[str, bool, str]]]:
    # 用双换行分割每段
    # 单换行分每行
    cdt = False
    note = ""
    functionList = []
    for lines in (await read_file(file_path=file_, mode="r", encoding="utf-8")).split("\n\n"):  # type: ignore
        funcGroup = []
        for line in lines.split("\n"):
            if line.strip().startswith("#"):
                if "cdt" in line.lower():
                    cdt = True
                note = line[1:].replace("cdt", "").strip()
            else:
                if "#" not in line:
                    funcGroup.append((line, cdt, note))
                else:
                    funcGroup.append(
                        (
                            line[: line.find("#")].strip(),
                            cdt,
                            line[line.find("#") + 1 :].strip() + note,
                        )
                    )
                cdt = False
                note = ""
        functionList.append(funcGroup)
    return functionList


write_2_file = on_alconna(
    Alconna(
        "写入文本文件",
        Option(
            "-n|-f|--file-name",
            default="新建文本文档",
            args=Args["file-name", str, "新建文本文档"],
        ),
        Option("-a|--append", default=False, action=store_true),
    ),
    aliases=(
        "write file",
        "write down",
        "写入",
        "write_file",
        "write_down",
        "write2file",
        "写入文件",
        "写入文本",
    ),
    rule=to_me(),
    # ignorecase=True,
)


@write_2_file.handle()
async def _(
    result: Arparma,
    event: T_MessageEvent,
    bot: T_Bot,
):

    nonebot.logger.info(result.options)

    usr_id = event.get_user_id()
    ulang = get_user_lang(usr_id)

    whole_texts = event.get_plaintext().split("\n", 1)

    if len(whole_texts) < 2:
        await write_2_file.finish(ulang.get("writefile.no_text"))

    file_2_write = (
        result.options["file-name"].args["file-name"]
        if result.options["file-name"].args
        else "新建文本文档"
    ) + ".txt"

    file_path = get_stored_path(usr_id, file_2_write, superuser=False)

    if result.options["append"].value:
        if file_2_write in filesaves[usr_id].keys():
            with file_path.open(mode="a", encoding="utf-8") as f:
                f.write(whole_texts[1])
            file_size = os.path.getsize(file_path)
            filesaves[usr_id]["totalSize"] += (
                file_size - filesaves[usr_id][file_2_write]["size"]
            )
            filesaves[usr_id][file_2_write]["size"] = file_size
            await write_2_file.finish(
                ulang.get(
                    "writefile.append_success",
                    NAME=file_2_write,
                    COUNT=len(whole_texts[1]),
                    SIZE=file_size,
                )
            )
        else:
            await write_2_file.finish(ulang.get("writefile.file_not_exist"))
    else:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(whole_texts[1])
        now = zhDateTime.DateTime.now()
        file_size = os.path.getsize(file_path)
        try:
            filesaves[usr_id][file_2_write] = {
                "date": [
                    now.year,
                    now.month,
                    now.day,
                    now.hour,
                    now.minute,
                ],
                "size": file_size,
            }
            filesaves[usr_id]["totalSize"] += file_size
        except KeyError:
            filesaves[usr_id] = {
                file_2_write: {
                    "date": [
                        now.year,
                        now.month,
                        now.day,
                        now.hour,
                        now.minute,
                    ],
                    "size": file_size,
                }
            }
            filesaves[usr_id]["totalSize"] = file_size
        save_filesaves()
        await write_2_file.finish(
            ulang.get(
                "writefile.write_success",
                NAME=file_2_write,
                SIZE=file_size,
            )
        )


cmd2struct = on_alconna(
    Alconna(
        "指令转结构",
        Option("-n|-f|--file-name", default="all", args=Args["file-name", str, "all"]),
        Option("-t|-type", default="all", args=Args["type", str, "all"]),
        Option(
            "-e|-x|--expand-axis", default="z+", args=Args["expand-axis", str, "z+"]
        ),
        Option("-l|--length-limit", default=32, args=Args["length-limit", int, 32]),
        Option(
            "-a|--author",
            default="DefaultUser",
            args=Args["author", str, "DefaultUser"],
        ),
    ),
    aliases={
        "函数转结构",
        "cmd2struct",
        "command2structure",
        "mcfunction2struct",
        "mcfunction2structure",
        "mcfunction转结构",
    },
)


@cmd2struct.handle()
async def _(
    result: Arparma,
    event: GroupMessageEvent | PrivateMessageEvent,
    bot: T_Bot,
):
    nonebot.logger.info(result.options)

    usr_id = event.get_user_id()

    ulang = get_user_lang(usr_id)

    superuser_permission = await SUPERUSER(bot, event)

    if ((qres := query_convert_points(usr_id, "structure"))[0] is False) and (
        not superuser_permission
    ):
        await cmd2struct.finish(
            UniMessage.text(
                ulang.get(
                    "convet.not_enough_point",
                    NOW=qres[1],
                    TOTAL=configdict["maxPersonConvert"]["structure"],
                )
            ),
            at_sender=True,
        )

    dest_axis = (
        result.options["expand-axis"].args["expand-axis"]
        if result.options["expand-axis"].args
        else "z+"
    ).lower()

    if len(dest_axis) == 2 and dest_axis[0] in (x, y, z) and dest_axis[1] in ("-", "+"):
        axis_forward = True if dest_axis[1] == "+" else False
        dest_axis = dest_axis[0]
    else:
        await cmd2struct.finish(
            UniMessage.text(
                ulang.get(
                    "cmd2struct.axis_wrong",
                ),
            ),
            at_sender=True,
        )

    dest_type = (
        result.options["type"].args["type"] if result.options["type"].args else "all"
    ).lower()

    if dest_type == "all":
        dest_type = ("bdx",)
    elif dest_type in [
        "bdx",
    ]:
        dest_type = ("bdx",)
    else:
        await cmd2struct.finish(
            UniMessage.text(
                ulang.get(
                    "convert.something_not_exist",
                    WHAT="转换格式",
                    NAME=dest_type,
                )
            ),
            at_sender=True,
        )
        return

    file_2_cvt = (
        result.options["file-name"].args["file-name"]
        if result.options["file-name"].args
        else "all"
    )

    if ((not superuser_permission) and (usr_id not in filesaves.keys())) or (
        superuser_permission
        and (
            (not len(filesaves))
            or (file_2_cvt.lower() == "all" and usr_id not in filesaves.keys())
        )
    ):
        await cmd2struct.finish(
            UniMessage.text(ulang.get("convert.no_file", TYPE="文本指令")),
            at_sender=True,
        )
        return
    else:
        if file_2_cvt == "all":
            file_2_cvt = [
                i for i in filesaves[usr_id].keys() if i.endswith(".mcfunction")
            ]
        else:
            file_2_cvt = file_2_cvt.split("&")

    length_limit = (
        result.options["length-limit"].args["length-limit"]
        if result.options["length-limit"].args
        else 32
    )

    author_name = (
        result.options["author"].args["author"]
        if result.options["author"].args
        else "DefaultUser"
    )

    # usr_data_path = database_dir / usr_id
    (usr_temp_path := temporary_dir / usr_id).mkdir(exist_ok=True)

    # 重定向标准输出
    buffer = StringIO()
    sys.stdout = buffer
    sys.stderr = buffer

    def go_chk_point() -> bool:
        res, pnt = query_convert_points(
            usr_id,
            "structure",
            random.random() % 0.4 + 0.1,
        )
        if not res:
            buffer.write(ulang.get("convert.break.not_enough_point", NOW=pnt))
        return res

    await cmd2struct.send(UniMessage.text(ulang.get("convert.start")))

    try:

        all_files: dict[str, dict[str, dict[str, int | tuple | str | list]]] = {}

        for file_to_convert in file_2_cvt:

            nonebot.logger.info("载入转换文件：{}".format(file_to_convert))

            to_convert_path = get_stored_path(
                usr_id, file_to_convert, superuser_permission
            )

            if to_convert_path.is_file():
                all_files[to_convert_path.name] = {}
            else:
                buffer.write("文件 {} 不存在\n".format(file_to_convert))
                continue

            cmd_lines = await read_file_into_command_lines(to_convert_path)

            if go_chk_point() and "bdx" in dest_type:
                if (
                    res := command_to_multiline_BDX_structure_file(
                        cmd_lines,
                        axis_=dest_axis,
                        forward_=axis_forward,
                        limit_=length_limit,
                        author=author_name,
                        outfile=usr_temp_path / file_to_convert / ".bdx",
                    )
                )[0]:
                    all_files[file_to_convert]["bdx"] = {
                        "指令总长度": res[1],
                        "结构总大小": res[2],
                    }
                else:
                    buffer.write("转换BDX文件出现错误。")

        if not all_files:
            nonebot.logger.warning(
                "无可供转换的文件",
            )
            await cmd2struct.finish(
                UniMessage(
                    "我相信质量守恒定律的存在，可是你却要把这份坚信给摧毁。\n*所指向之文件皆不存在"
                )
            )

    except Exception as e:
        nonebot.logger.error("转换存在错误：{}".format(e))
        buffer.write(
            "[ERROR] {}\n".format(e).replace(str(Path(__file__).parent.resolve()), "[]")
        )

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    compress_zipfile(
        usr_temp_path,
        fp := str(
            (
                temporary_dir
                / (fn := "struct[{}]-{}.zip".format(hanzi_timeid(), usr_id))
            ).resolve()
        ),
    )

    shutil.rmtree(usr_temp_path)

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

    await cmd2struct.finish(
        UniMessage.text(
            "转换结束，当前剩余转换点数：⌊p⌋≈{:.2f}|{}".format(
                query_convert_points(
                    usr_id,
                    "structure",
                    0,
                )[1],
                configdict["maxPersonConvert"]["structure"],
            )
        ),
        at_sender=True,
    )
