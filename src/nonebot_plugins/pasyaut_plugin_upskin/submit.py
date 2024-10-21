import nonebot
import nonebot.adapters
import nonebot.drivers
import nonebot.rule

from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11.event import (
    GroupUploadNoticeEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)

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

from src.utils.base.ly_typing import T_Bot, T_MessageEvent


on_submit_help = on_alconna(
    command=Alconna("投稿帮助"),
    aliases={
        "查看投稿帮助",
        "投稿help",
        "submit_help",
        "sbm_hlp",
        "sbmhlp",
    },
    rule=nonebot.rule.to_me(),
)


@on_submit_help.handle()
async def _(
    event: GroupMessageEvent,
    bot: T_Bot,
):
    pass


on_submit_keyword = nonebot.on_keyword(
    keywords={"皮肤投稿", "皮肤上传", "皮肤代投", "皮肤代发"},
)


@on_submit_keyword.handle()
async def _(bot: T_Bot, event: T_MessageEvent):
    return
    await on_submit_keyword.finish(
        "请使用命令提交皮肤：\n" + "```\n" + "皮肤提交 [皮肤名] [图片]\n" + "```"
    )
