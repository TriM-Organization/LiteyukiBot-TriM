'''
    接龙
'''

import asyncio
from asyncio import TimerHandle

from typing import List, Dict, Any

import re
import random
import pypinyin
from pydantic import BaseModel

from nonebot.matcher import Matcher
from nonebot import on_regex, require
from nonebot.params import RegexDict
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from typing_extensions import Annotated

require("nonebot_plugin_alconna")
require("nonebot_plugin_session")



from nonebot_plugin_alconna import (
    Alconna,
    AlconnaQuery,
    Option,
    Query,
    Text,
    UniMessage,
    on_alconna,
    store_true,
)
from nonebot.rule import to_me
from nonebot_plugin_session import SessionId, SessionIdType

from .utils import random_idiom, legal_idiom, legal_patted_idiom, get_idiom


__plugin_meta__ = PluginMetadata(
    name="接龙",
    description="汉字词语或成语接龙",
    usage=(
        "@我 + “接龙”开始游戏；\n"
        # "你有十次的机会猜一个四字词语；\n"
        # "每次猜测后，汉字与拼音的颜色将会标识其与正确答案的区别；\n"
        # "青色 表示其出现在答案中且在正确的位置；\n"
        # "橙色 表示其出现在答案中但不在正确的位置；\n"
        # "每个格子的 汉字、声母、韵母、声调 都会独立进行颜色的指示。\n"
        # "当四个格子都为青色时，你便赢得了游戏！\n"
        # "可发送“结束”结束游戏；可发送“提示”查看提示。\n"
        # "使用 --strict 选项开启非默认的成语检查，即猜测的短语必须是成语，\n"
        # "如：@我 猜成语 --strict"
    ),
    type="application",
    # homepage="https://github.com/noneplugin/nonebot-plugin-handle",
    # config=Config,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna", "nonebot_plugin_session"
    ),
    extra={
        "example": "@小羿 接龙",
    },
)




# games: Dict[str, Dragle] = {}
games = {}
auto_echo = {}
timers: Dict[str, TimerHandle] = {}

UserId = Annotated[str, SessionId(SessionIdType.GROUP)]


def game_is_running(user_id: UserId) -> bool:
    return user_id in games


def game_not_running(user_id: UserId) -> bool:
    return user_id not in games


handle = on_alconna(
    Alconna("dockdragon", Option("-s|--strict", default=False, action=store_true)),
    aliases=("接龙",),
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
    aliases=("结束游戏", "结束接龙"),
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

def is_auto_echo(user_id: UserId) -> bool:
    return auto_echo.get(user_id, True)


handle_idiom = on_regex(
    r"^(?P<idiom>[\u4e00-\u9fa5]{4})$",
    rule=is_auto_echo,
    block=True,
    priority=14,
)


停止自动回复 = on_alconna(
    "自动接龙",
    aliases=("自动成语接龙",),
    rule=None,
    use_cmd_start=True,
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
        msg = "接龙超时，游戏结束。"
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



# @handle.handle()
# async def _(
#     matcher: Matcher,
#     user_id: UserId,
#     strict: Query[bool] = AlconnaQuery("strict.value", False),
# ):
#     # is_strict = handle_config.handle_strict_mode or strict.result
#     idiom, explanation = random_idiom()
#     game = Handle(idiom, explanation, strict=is_strict)

#     games[user_id] = game
#     set_timeout(matcher, user_id)

#     msg = Text(
#         f"你有{game.times}次机会猜一个四字成语，"
#         + ("发送有效成语以参与游戏。" if is_strict else "发送任意四字词语以参与游戏。")
#     ) + Image(raw=await run_sync(game.draw)())
#     await msg.send()


@停止自动回复.handle()
async def _(matcher: Matcher, user_id: UserId):
    if auto_echo.get(user_id, True):
        auto_echo[user_id] = False
        await matcher.finish("已关闭自动接龙回复")
    else:
        auto_echo[user_id] = True
        await matcher.finish("已开启自动接龙回复")



@handle_idiom.handle()
async def _(matcher: Matcher, user_id: UserId, matched: Dict[str, Any] = RegexDict()):
    # game = games[user_id]
    # set_timeout(matcher, user_id)

    idiom = str(matched["idiom"])
    # result = game.guess(idiom)

    if legal_idiom(idiom):
        # stop_game(user_id)
        print(matcher.get_target())
        await matcher.finish(get_idiom(idiom,True,True))

    # elif result == GuessResult.DUPLICATE:
    #     await matcher.finish("你已经猜过这个成语了呢")

    # elif result == GuessResult.ILLEGAL:
    #     await matcher.finish(f"你确定“{idiom}”是个成语吗？")

    # else:
    #     await UniMessage.image(raw=await run_sync(game.draw)()).send()




# zh = re.compile(r"[\u4e00-\u9fff]+")


# @cat.on_text(states=["", "idle"])
# async def handled():
#     '''自动接龙'''
#     text = cat.arg
#     r = zh.search(text)
#     if not r:
#         return

#     word = r.group()

#     for dragon in dragon_list:
#         # 跳过不启用的接龙
#         if not dragon.use:
#             continue

#         # 当前词语符合接龙词库
#         if dragon.check(word):

#             # 上次接龙
#             last = cat.cache.get("dragon", {}).get(dragon.name, "")

#             # 成功接龙
#             if last and word:
#                 p1 = lazy_pinyin(last)[-1]
#                 p2 = lazy_pinyin(word)[0]
#                 if p1 == p2:
#                     await cat.send(f"[{cat.user.name}] 接龙成功！")


#             # 无论是否成功接龙都发送下一个词
#             word = dragon.next(word)
#             cat.cache.setdefault("dragon", {})
#             cat.cache["dragon"][dragon.name] = word
#             if not word:
#                 word = choice(["%$#*-_", "你赢了", "接不上来..."])
#             await cat.send(word)
#             break


# cat.set_wakeup_cmds(cmds="接龙管理")
# cat.set_rest_cmds(cmds=["exit", "退出"])


# @cat.on_cmd(cmds="list", states="idle")
# async def list_all():
#     '''列出所有词库'''
#     items = ["所有词库："]
#     for dragon in dragon_list:
#         if dragon.use:
#             items.append(f"[{dragon.name}] 正在使用")
#         else:
#             items.append(f"[{dragon.name}]")
#     await cat.send("\n".join(items))


# @cat.on_cmd(cmds="data", states="idle")
# async def show_data():
#     '''展示你的答题数据'''
#     gid = cat.group.id
#     uid = cat.user.id

#     stmt = select(DragonUserData).filter_by(group_id=gid, user_id=uid)
#     cursor = cat.db_session.exec(stmt)
#     user_datas = cursor.all()

#     if user_datas:
#         info = "\n".join(
#             f"[{u.dragon_name}] 接龙次数 {u.cnt}"
#             for u in user_datas
#         )
#     else:
#         info = "你还没有用过我...T_T"

#     await cat.send(info)

