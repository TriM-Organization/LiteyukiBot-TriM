import platform
import time

import nonebot
import psutil
from cpuinfo import cpuinfo
from nonebot.adapters import satori

from liteyuki import __version__
from liteyuki.utils import for_in
from src.utils import __NAME__
from src.utils.base.config import get_config
from src.utils.base.data_manager import TempConfig, common_db
from src.utils.base.language import Language
from src.utils.base.resource import get_loaded_resource_packs, get_path
from src.utils.message.html_tool import template2image, md_to_pic
from src.utils import satori_utils
from .counter_for_satori import satori_counter
from git import Repo

# require("nonebot_plugin_apscheduler")
# from nonebot_plugin_apscheduler import scheduler

commit_hash = Repo(".").head.commit.hexsha

protocol_names = {
    0: "苹果iPad",
    1: "安卓掌机",
    2: "安卓穿戴",
    3: "Mac主机",
    5: "苹果iPad",
    6: "安卓平板",
}


"""
Universal Interface
data
- bot
  - name: str
    icon: str
    id: int
    protocol_name: str
    groups: int
    friends: int
    message_sent: int
    message_received: int
    app_name: str
- hardware
    - cpu
        - percent: float
        - name: str
    - mem
        - percent: float
        - total: int
        - used: int
        - free: int
    - swap
        - percent: float
        - total: int
        - used: int
        - free: int
    - disk: list
        - name: str
        - percent: float
        - total: int
"""
# status_card_cache = {}  # lang -> bytes


# 60s刷新一次
# 之前写的什么鬼玩意，这么重要的功能这样写？？？
# @scheduler.scheduled_job("cron", second="*/40")
# async def refresh_status_card():
#     nonebot.logger.debug("Refreshing status card cache.")
#     global status_card_cache
#     status_card_cache = {}
# bot_data = await get_bots_data()
# hardware_data = await get_hardware_data()
# liteyuki_data = await get_liteyuki_data()
# for lang in status_card_cache.keys():
#     status_card_cache[lang] = await generate_status_card(
#         bot_data,
#         hardware_data,
#         liteyuki_data,
#         lang=lang,
#         use_cache=False
#     )


# 用markdown文字展示状态卡片
async def generate_status_card_markdown(
    bot: dict,
    hardware: dict,
    liteyuki: dict,
    lang="zh-CN",
    motto={"text": "风朗气清", "source": "成语一则"},
) -> bytes:
    from .md_status_utils import (
        markdown_status_bot_card_text,
        markdown_status_card_text,
        markdown_status_disk_card_text,
        convert_size,
        seconds2texttime,
    )

    local_dt = await get_local_data(lang)
    bytes_suffix = " X" + local_dt["units"]["Byte"]
    bin_units = local_dt["units"]["Bin_Units"]

    markdown_status_bot_card_text__ = (
        markdown_status_bot_card_text.replace(
            r"{local_groups}",
            local_dt["groups"],
        )
        .replace(
            r"{local_friends}",
            local_dt["friends"],
        )
        .replace(
            r"{local_message_sent}",
            local_dt["message_sent"],
        )
        .replace(
            r"{local_message_received}",
            local_dt["message_received"],
        )
    )

    markdown_status_disk_card_text__ = (
        markdown_status_disk_card_text.replace(
            r"{local_used}",
            local_dt["used"],
        )
        .replace(
            r"{local_free}",
            local_dt["free"],
        )
        .replace(
            r"{local_total}",
            local_dt["total"],
        )
    )

    fnl_text = markdown_status_card_text.format(
        local_description=local_dt["description"],
        liteyuki_name=liteyuki["name"],
        liteyuki_version=liteyuki["version"],
        liteyuki_nonebot=liteyuki["nonebot"],
        liteyuki_system=liteyuki["system"],
        liteyuki_python=liteyuki["python"],
        local_plugins=local_dt["plugins"],
        liteyuki_plugins=liteyuki["plugins"],
        local_resources=local_dt["resources"],
        liteyuki_resources=liteyuki["resources"],
        local_bots=local_dt["bots"],
        liteyuki_bots=liteyuki["bots"],
        local_runtime=local_dt["runtime"],
        liteyuki_runtime=seconds2texttime(
            liteyuki["runtime"],
            unit_days=local_dt["days"],
            unit_hours=local_dt["hours"],
            unit_minutes=local_dt["minutes"],
            unit_seconds=local_dt["seconds"],
        ),
        for_bots="\n".join(
            [
                markdown_status_bot_card_text__.format(
                    bot_name=s_bot["name"],
                    bot_icon=s_bot["icon"],
                    bot_app_name=s_bot["app_name"],
                    bot_protocol_name=s_bot["protocol_name"],
                    bot_groups=s_bot["groups"],
                    bot_friends=s_bot["friends"],
                    bot_message_sent=s_bot["message_sent"],
                    bot_message_received=s_bot["message_received"],
                )
                for s_bot in bot["bots"]
            ]
        ),
        local_cpu=local_dt["cpu"],
        hardware_cpu_percent=hardware["cpu"]["percent"],
        hardware_cpu_name=hardware["cpu"]["name"],
        hardware_cpu_cores=hardware["cpu"]["cores"],
        local_cores=local_dt["cores"],
        hardware_cpu_threads=hardware["cpu"]["threads"],
        local_threads=local_dt["threads"],
        hardware_cpu_freq=hardware["cpu"]["freq"] / 1000,
        local_units_GHz=local_dt["units"]["GHz"],
        local_memory=local_dt["memory"],
        hardware_memory_percent=hardware["memory"]["percent"],
        local_process=local_dt["process"],
        hardware_memory_processmem=convert_size(
            hardware["memory"]["usedProcess"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        local_used=local_dt["used"],
        hardware_memory_usedmem=convert_size(
            hardware["memory"]["used"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        local_free=local_dt["free"],
        hardware_memory_freemem=convert_size(
            hardware["memory"]["free"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        local_total=local_dt["total"],
        hardware_memory_totalmem=convert_size(
            hardware["memory"]["total"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        local_swap=local_dt["swap"],
        hardware_swap_percent=hardware["swap"]["percent"],
        hardware_swap_usedswap=convert_size(
            hardware["swap"]["used"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        hardware_swap_freeswap=convert_size(
            hardware["swap"]["free"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        hardware_swap_totalswap=convert_size(
            hardware["swap"]["total"],
            precision=2,
            is_unit_added=True,
            suffix=bytes_suffix,
            bin_units=bin_units,
        ),
        local_disk=local_dt["disk"],
        for_disk="\n".join(
            [
                markdown_status_disk_card_text__.format(
                    hardware_disk_name=s_disk["name"],
                    hardware_disk_percent=s_disk["percent"],
                    hardware_disk_useddisk=convert_size(
                        s_disk["used"],
                        precision=2,
                        is_unit_added=True,
                        suffix=bytes_suffix,
                        bin_units=bin_units,
                    ),
                    hardware_disk_freedisk=convert_size(
                        s_disk["free"],
                        precision=2,
                        is_unit_added=True,
                        suffix=bytes_suffix,
                        bin_units=bin_units,
                    ),
                    hardware_disk_totaldisk=convert_size(
                        s_disk["total"],
                        precision=2,
                        is_unit_added=True,
                        suffix=bytes_suffix,
                        bin_units=bin_units,
                    ),
                )
                for s_disk in hardware["disk"]
            ]
        ),
        motto_text=motto["text"],
        motto_source=motto["source"],
        acknowledgement=get_config("status_acknowledgement"),
    )

    return await md_to_pic(fnl_text, width=540, device_scale_factor=4)


# def gogop(x):
#     from rich.console import Console
#     Console().print(x)
#     return x


# 获取状态卡片
# bot_id 参数已经是bot参数的一部分了，不需要保留，但为了“兼容性”……
async def generate_status_card(
    bot: dict,
    hardware: dict,
    liteyuki: dict,
    lang="zh-CN",
    motto={"text": "风朗气清", "source": "成语一则"},
    bot_id="0",  # 兼容性
) -> bytes:
    # print(get_config("status_acknowledgement"))
    return await template2image(
        get_path("templates/status.html", abs_path=True),
        {
            "data": {
                "bot": bot,
                "hardware": hardware,
                "liteyuki": liteyuki,
                "localization": await get_local_data(lang),
                "motto": motto,
                "acknowledgement": get_config("status_acknowledgement"),
            }
        },
    )


async def get_local_data(lang_code) -> dict:
    lang = Language(lang_code)
    bin_forcase = lang.get("status.unit.binary_middile")
    return {
        "friends": lang.get("status.friends"),
        "groups": lang.get("status.groups"),
        "plugins": lang.get("status.plugins"),
        "bots": lang.get("status.bots"),
        "message_sent": lang.get("status.message_sent"),
        "message_received": lang.get("status.message_received"),
        "cpu": lang.get("status.cpu"),
        "memory": lang.get("status.memory"),
        "swap": lang.get("status.swap"),
        "disk": lang.get("status.disk"),
        "usage": lang.get("status.usage"),
        "total": lang.get("status.total"),
        "used": lang.get("status.used"),
        "free": lang.get("status.free"),
        "days": lang.get("status.days"),
        "hours": lang.get("status.hours"),
        "minutes": lang.get("status.minutes"),
        "seconds": lang.get("status.seconds"),
        "runtime": lang.get("status.runtime"),
        "threads": lang.get("status.threads"),
        "cores": lang.get("status.cores"),
        "process": lang.get("status.process"),
        "resources": lang.get("status.resources"),
        "description": lang.get("status.description"),
        "units": {
            "GHz": lang.get("status.unit.GHz"),
            "Byte": lang.get("status.unit.Byte"),
            "Bin_Units": [
                (
                    ((bin_forcase + i) if "zh" in lang_code else (i + bin_forcase))
                    if i.strip()
                    else ""
                )
                for i in lang.get("status.unit.Bit_Units").split(";")
            ],
        },
    }


async def get_bots_data(self_id: str = "0") -> dict:
    """获取当前所有机器人数据
    Returns:
    """
    result = {
        "self_id": self_id,
        "bots": [],
    }
    for bot_id, bot in nonebot.get_bots().items():
        groups = 0
        friends = 0
        status = {}
        bot_name = bot_id
        version_info = {}
        if isinstance(bot, satori.Bot):
            try:
                bot_name = (await satori_utils.user_infos.get(bot.self_id)).name
                groups = str(await satori_utils.count_groups(bot))
                friends = str(await satori_utils.count_friends(bot))
                status = {}
                version_info = await bot.get_version_info()  # type: ignore
            except Exception:
                pass
        else:
            try:
                # API fetch
                bot_name = (await bot.get_login_info())["nickname"]
                groups = len(await bot.get_group_list())
                friends = len(await bot.get_friend_list())
                status = await bot.get_status()
                version_info = await bot.get_version_info()
            except Exception:
                pass

        statistics = status.get("stat", {})
        app_name = version_info.get("app_name", "未知应用接口")
        if app_name in ["Lagrange.OneBot", "LLOneBot", "Shamrock", "NapCat.Onebot"]:
            icon = f"https://q.qlogo.cn/g?b=qq&nk={bot_id}&s=640"
        elif isinstance(bot, satori.Bot):
            app_name = "Satori"
            icon = (await bot.login_get()).user.avatar
        else:
            icon = None
        bot_data = {
            "name": bot_name,
            "icon": icon,
            "id": bot_id,
            "protocol_name": protocol_names.get(
                version_info.get("protocol_name"), "在线"
            ),
            "groups": groups,
            "friends": friends,
            "message_sent": (
                satori_counter.msg_sent
                if isinstance(bot, satori.Bot)
                else statistics.get("message_sent", 0)
            ),
            "message_received": (
                satori_counter.msg_received
                if isinstance(bot, satori.Bot)
                else statistics.get("message_received", 0)
            ),
            "app_name": app_name,
        }
        result["bots"].append(bot_data)

    return result


async def get_hardware_data(lang_code) -> dict:
    lang = Language(lang_code)
    mem = psutil.virtual_memory()
    all_processes = psutil.Process().children(recursive=True)
    all_processes.append(psutil.Process())

    mem_used_process = 0
    process_mem = {}
    for process in all_processes:
        try:
            ps_name = process.name().replace(".exe", "")
            if ps_name not in process_mem:
                process_mem[ps_name] = 0
            process_mem[ps_name] += process.memory_info().rss
            mem_used_process += process.memory_info().rss
        except Exception:
            pass
    swap = psutil.swap_memory()
    cpu_infos = cpuinfo.get_cpu_info()
    cpu_brand_raw = cpu_infos.get(
        "hardware_raw",
        cpu_infos.get("brand_raw", "未知处理器"),  # 此处之汉文不会被直接使用
    ).lower()
    if cpu_brand_selected := for_in(
        ("amd", "intel", "apple", "qualcomm", "mediatek", "samsung", "nvidia"),
        cpu_brand_raw,
    ):
        brand = lang.get("status.cpubrand." + cpu_brand_selected[0])
    else:
        brand = lang.get("status.cpubrand.unknown")
    result = {
        "cpu": {
            "percent": psutil.cpu_percent(),
            "name": "{} {}".format(
                brand, cpu_infos.get("arch_string_raw", lang.get("status.arch.unknown"))
            ),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "freq": psutil.cpu_freq().current,  # 单位 MHz
        },
        "memory": {
            "percent": mem.percent,
            "total": mem.total,
            "used": mem.used,
            "free": mem.free,
            "usedProcess": mem_used_process,
        },
        "swap": {
            "percent": swap.percent,
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
        },
        "disk": [],
    }

    other_disk = {
        "name": lang.get("status.disk.other"),
        "percent": 0,
        "total": 0,
        "used": 0,
        "free": 0,
    }
    for disk in psutil.disk_partitions(all=True):
        try:
            disk_usage = psutil.disk_usage(disk.mountpoint)
            if disk_usage.total == 0 or disk.mountpoint.startswith(
                ("/var", "/boot", "/run", "/proc", "/sys", "/dev", "/tmp", "/snap")
            ):
                other_disk["percent"] = (other_disk["percent"] + disk_usage.percent) / 2
                other_disk["total"] += disk_usage.total
                other_disk["used"] += disk_usage.used
                other_disk["free"] += disk_usage.free
            else:
                result["disk"].append(
                    {
                        "name": disk.mountpoint,
                        "percent": disk_usage.percent,
                        "total": disk_usage.total,
                        "used": disk_usage.used,
                        "free": disk_usage.free,
                    }
                )
        except:
            pass

    if other_disk["total"] > 0:  # 避免除零错误
        result["disk"].append(other_disk)

    return result


async def get_liteyuki_data() -> dict:
    temp_data: TempConfig = common_db.where_one(TempConfig(), default=TempConfig())
    result = {
        "name": list(get_config("nickname", [__NAME__]))[0],
        "version": f"{__version__}{'-' + commit_hash[:7] if (commit_hash and len(commit_hash) > 8) else ''}",
        "plugins": len(nonebot.get_loaded_plugins()),
        "resources": len(get_loaded_resource_packs()),
        "nonebot": f"{nonebot.__version__}",
        "python": f"{platform.python_implementation()} {platform.python_version()}",
        "system": f"{platform.system()} {platform.release()}",
        "runtime": time.time()
        - temp_data.data.get("start_time", time.time()),  # 运行时间秒数
        "bots": len(nonebot.get_bots()),
    }
    return result
