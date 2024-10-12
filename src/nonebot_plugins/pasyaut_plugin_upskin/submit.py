

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


on_convert_help = on_alconna(
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


@on_convert_help.handle()
async def _(
    event: GroupMessageEvent,
    bot: T_Bot,
):
    pass
