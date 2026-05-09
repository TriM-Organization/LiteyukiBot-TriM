import asyncio
from asyncio import TimerHandle
from typing import Any, Dict
from typing_extensions import Annotated

import nonebot
from nonebot import on_regex, require, on_command
from nonebot.matcher import Matcher
from nonebot.params import RegexDict
from nonebot.plugin import PluginMetadata, inherit_supported_adapters
from nonebot.rule import to_me
from nonebot.utils import run_sync
from nonebot.permission import SUPERUSER

import json

require("nonebot_plugin_alconna")
require("nonebot_plugin_session")

from nonebot_plugin_alconna import (
    Alconna,
    AlconnaQuery,
    Image,
    Option,
    Query,
    Text,
    UniMessage,
    on_alconna,
    store_true,
    Args,
    Arparma,
)
from nonebot_plugin_session import SessionId, SessionIdType

from src.utils.base.ly_typing import T_Bot

from .config import Config, handle_config
from .data_source import GuessResult, Handle
from .utils import (
    random_idiom,
    HANDLE_ANSWER_PHRASES,
    HANDLE_HARD_ANSWER_PHRASES,
    HANDLE_LEGAL_PHRASES,
    handle_answer_hard_path,
    handle_answer_path,
    handle_idiom_path,
)

__plugin_meta__ = PluginMetadata(
    name="猜成语",
    description="猜成语-睿乐特别版",
    usage=(
        "@我 + “猜成语”开始游戏；\n"
        "你有十次的机会猜一个四字词语；\n"
        "每次猜测后，汉字与拼音的颜色将会标识其与正确答案的区别；\n"
        "青色 表示其出现在答案中且在正确的位置；\n"
        "橙色 表示其出现在答案中但不在正确的位置；\n"
        "每个格子的 汉字、声母、韵母、声调 都会独立进行颜色的指示。\n"
        "当四个格子都为青色时，你便赢得了游戏！\n"
        "可发送“结束”结束游戏；可发送“提示”查看提示。\n"
        "使用 --strict 选项开启非默认的成语检查，即猜测的短语必须是成语，\n"
        "如：@我 猜成语 --strict\n"
        "使用 --hard 选项开启困难词库\n"
        "管理员可以使用 新成语、成语答案 两个命令进行成语词库添加和答案查看"
    ),
    type="application",
    homepage="https://github.com/noneplugin/nonebot-plugin-handle",
    config=Config,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna", "nonebot_plugin_session"
    ),
    extra={
        "example": "@小Q 猜成语",
    },
)


games: Dict[str, Handle] = {}
timers: Dict[str, TimerHandle] = {}

UserId = Annotated[str, SessionId(SessionIdType.GROUP)]


def game_is_running(user_id: UserId) -> bool:
    return user_id in games


def game_not_running(user_id: UserId) -> bool:
    return user_id not in games


handle = on_alconna(
    Alconna(
        "handle",
        Option("-s|--strict", default=False, action=store_true),
        Option("-d|--hard", default=False, action=store_true),
    ),
    aliases=("猜成语",),
    rule=to_me() & game_not_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)
handle_hint = on_alconna(
    "提示",
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)
handle_stop = on_alconna(
    "结束",
    aliases=("结束游戏", "结束猜成语"),
    rule=game_is_running,
    use_cmd_start=True,
    block=True,
    priority=13,
)


# handle_update = on_alconna(
#     "更新词库",
#     aliases=("刷新词库", "猜成语刷新词库"),
#     rule=to_me(),
#     use_cmd_start=True,
#     block=True,
#     priority=13,
# )


handle_idiom = on_regex(
    r"^(?P<idiom>[\u4e00-\u9fa5]{4})$",
    rule=game_is_running,
    block=True,
    priority=14,
)


def stop_game(user_id: str):
    if timer := timers.pop(user_id, None):
        timer.cancel()
    games.pop(user_id, None)


async def stop_game_timeout(matcher: Matcher, user_id: str):
    game = games.get(user_id, None)
    stop_game(user_id)
    if game:
        msg = "猜成语超时，游戏结束。"
        if len(game.guessed_idiom) >= 1:
            msg += f"\n{game.result}"
        await matcher.finish(msg)


def set_timeout(matcher: Matcher, user_id: str, timeout: float = 300):
    if timer := timers.get(user_id, None):
        timer.cancel()
    loop = asyncio.get_running_loop()
    timer = loop.call_later(
        timeout, lambda: asyncio.ensure_future(stop_game_timeout(matcher, user_id))
    )
    timers[user_id] = timer


@handle.handle()
async def _(
    result: Arparma,
    matcher: Matcher,
    user_id: UserId,
):
    nonebot.logger.info(result.options)
    is_strict = handle_config.handle_strict_mode or result.options["strict"].value
    idiom, explanation = random_idiom(result.options["hard"].value)
    game = Handle(idiom, explanation, strict=is_strict)

    games[user_id] = game
    set_timeout(matcher, user_id)

    msg = Text(
        f"你有{game.times}次机会猜一个四字成语，"
        + ("发送有效成语以参与游戏。" if is_strict else "发送任意四字词语以参与游戏。")
    ) + Image(raw=await run_sync(game.draw)())
    await msg.send()


@handle_hint.handle()
async def _(matcher: Matcher, user_id: UserId):
    game = games[user_id]
    set_timeout(matcher, user_id)

    await UniMessage.image(raw=await run_sync(game.draw_hint)()).send()


@handle_stop.handle()
async def _(matcher: Matcher, user_id: UserId):
    game = games[user_id]
    stop_game(user_id)

    msg = "游戏已结束"
    if len(game.guessed_idiom) >= 1:
        msg += f"\n{game.result}"
    await matcher.finish(msg)


# @handle_update.handle()


@handle_idiom.handle()
async def _(matcher: Matcher, user_id: UserId, matched: Dict[str, Any] = RegexDict()):
    game = games[user_id]
    set_timeout(matcher, user_id)

    idiom = str(matched["idiom"])
    result = game.guess(idiom)

    if result in [GuessResult.WIN, GuessResult.LOSS]:
        stop_game(user_id)
        msg = Text(
            (
                "恭喜你猜出了成语！"
                if result == GuessResult.WIN
                else "很遗憾，没有人猜出来呢"
            )
            + f"\n{game.result}"
        ) + Image(raw=await run_sync(game.draw)())
        await msg.send()

    elif result == GuessResult.DUPLICATE:
        await matcher.finish("你已经猜过这个成语了呢")

    elif result == GuessResult.ILLEGAL:
        await matcher.finish(f"你确定“{idiom}”是个成语吗？")

    else:
        await UniMessage.image(raw=await run_sync(game.draw)()).send()


handle_update_idiom = on_alconna(
    Alconna(
        "新成语",
        Option(
            "-e|--explanation",
            default="",
            args=Args["explanation", str, "未提供该成语的解释说明"],
        ),
        Option(
            "-d|--hard",
            default=False,
            action=store_true,
        ),
        Args["idiom", str, ""],
    ),
    aliases=("新增成语", "猜成语新增成语"),
    use_cmd_start=True,
    permission=SUPERUSER,
    block=True,
    priority=13,
)


@handle_update_idiom.handle()
async def _(
    result: Arparma,
    matcher: Matcher,
    user_id: UserId,
    bot: T_Bot,
):

    try:
        if result.options["explanation"].args["explanation"]:
            explanation = result.options["explanation"].args["explanation"]
        else:
            nonebot.logger.info("！！！！这里永远不可能被执行到")
            explanation = "未提供该成语的解释说明"
    except:
        explanation = None

    if hard := result.options["hard"].value:
        if not explanation:
            explanation = "未提供该成语的解释说明"

    if not (idiom := result.main_args["idiom"]):
        await handle_update_idiom.finish("请在命令后带上你要增加的成语")

    HANDLE_LEGAL_PHRASES.append(idiom)
    json.dump(
        HANDLE_LEGAL_PHRASES,
        handle_idiom_path.open("w", encoding="utf-8"),
        ensure_ascii=False,
        indent=4,
        sort_keys=True,
    )

    if explanation:
        if hard:
            HANDLE_HARD_ANSWER_PHRASES.append(
                {"word": idiom, "explanation": explanation}
            )
            json.dump(
                HANDLE_HARD_ANSWER_PHRASES,
                handle_answer_hard_path.open("w", encoding="utf-8"),
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            )
        else:
            HANDLE_ANSWER_PHRASES.append({"word": idiom, "explanation": explanation})
            json.dump(
                HANDLE_ANSWER_PHRASES,
                handle_answer_path.open("w", encoding="utf-8"),
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            )

    await handle_update_idiom.finish(
        "新增成功，当前词库总数：{}个\n可用普通模式成语：{}个\n可用困难模式成语：{}个".format(
            len(HANDLE_LEGAL_PHRASES),
            len(HANDLE_ANSWER_PHRASES),
            len(HANDLE_HARD_ANSWER_PHRASES),
        )
    )


handle_answer = on_alconna(
    Alconna(
        "成语答案",
        Option(
            "-g|--group",
            default="Now",
            args=Args["group", str, "Now"],
        ),
        Option(
            "-l|--list",
            default=False,
            action=store_true,
        ),
    ),
    aliases=("handle-answer", "猜成语答案"),
    # rule=game_is_running,
    use_cmd_start=True,
    permission=SUPERUSER,
    block=True,
    priority=13,
)


@handle_answer.handle()
async def _(
    result: Arparma,
    matcher: Matcher,
    user_id: UserId,
    bot: T_Bot,
):

    if result.options["list"].value:
        await handle_answer.finish(
            UniMessage.text(
                "\n".join(
                    "群{}，答案“{}”".format(i.split("_")[-1], j.idiom)
                    for i, j in games.items()
                )
            )
        )
        return

    try:
        if result.options["group"].args["group"] == "Now":
            session_numstr = user_id
        else:
            session_numstr = "qq_OneBot V11_{}_{}".format(
                bot.self_id, result.options["group"].args["group"]
            )
    except:
        session_numstr = user_id

    if session_numstr in games.keys():
        await handle_answer.finish(UniMessage.text(games[session_numstr].idiom))
    else:
        await handle_answer.finish(
            UniMessage.text("{} 不存在开局的游戏".format(session_numstr))
        )
