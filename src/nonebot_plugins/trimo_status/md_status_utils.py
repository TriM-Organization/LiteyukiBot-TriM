markdown_status_bot_card_text = """
### **{bot_name} &nbsp;|&nbsp; <img src="{bot_icon}" width="40">**

 - {bot_app_name} : {bot_protocol_name}
 - {local_groups}{bot_groups} | {local_friends}{bot_friends} | {local_message_sent}{bot_message_sent} | {local_message_received}{bot_message_received}
"""

markdown_status_disk_card_text = """ - {hardware_disk_name}

\t{local_used} {hardware_disk_useddisk} {hardware_disk_percent}% | {local_free} {hardware_disk_freedisk} | {local_total} {hardware_disk_totaldisk}"""

markdown_status_card_text = """
<h1 style="text-align: center;"> {local_description} </h1>

<h2> <img src="https://p.qlogo.cn/gh/861684859/861684859/" width="50" alt="bot-icon"> &nbsp; {liteyuki_name} - 睿乐 </h2>

 - 灵温 {liteyuki_version} | Nonebot {liteyuki_nonebot}
 - {liteyuki_system} {liteyuki_python}
 - {local_plugins}{liteyuki_plugins} | {local_resources}{liteyuki_resources} | {local_bots}{liteyuki_bots}
 - {local_runtime}{liteyuki_runtime}

{for_bots}

## {local_cpu} : {hardware_cpu_percent}%

 - {hardware_cpu_name} | {hardware_cpu_cores}{local_cores} {hardware_cpu_threads}{local_threads} | {hardware_cpu_freq}{local_units_GHz}


## {local_memory} : {hardware_memory_percent}%

 - {local_process} {hardware_memory_processmem}
 - {local_used} {hardware_memory_usedmem}
 - {local_free} {hardware_memory_freemem}
 - {local_total} {hardware_memory_totalmem}

## {local_swap} : {hardware_swap_percent}%

 - {local_used} {hardware_swap_usedswap}
 - {local_free} {hardware_swap_freeswap}
 - {local_total} {hardware_swap_totalswap}

## {local_disk}

{for_disk}

-----------------------

### {motto_text}

<div align="right">——{motto_source}</div>

#### <div align="center">{acknowledgement}</div>

#### <div align="center">该页样式由 <img src="https://q.qlogo.cn/g?b=qq&nk=3657522512&s=640" width=40>金羿Eilles 设计</div>
"""


def convert_size(
    size: int | float,
    precision: int = 2,
    is_unit_added: bool = True,
    suffix: str = " X字节",
    bin_units: list[str] = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi", "Yi"],
):
    """
    将字节转换为带单位的大小

    :param size: 要转换的字节大小
    :param precision: 保留小数位数
    :param is_unit_added: 是否添加单位
    :param suffix: 单位后缀
    :param bin_units: 单位列表
    :return: 转换后的大小字符串
    """
    is_negative = size < 0
    size = abs(size)
    # let units = ["", "千", "兆", "吉", "太", "拍", "艾", "泽"];
    unit = ""

    for sg_unit in bin_units:
        if size < 1024:
            unit = sg_unit
            break
        size /= 1024

    if is_negative:
        size = -size

    if is_unit_added:
        return ("{" + ":.{}f".format(precision) + "}").format(size) + suffix.replace(
            "X", unit
        )
    else:
        return size


def seconds2texttime(
    seconds: int,
    unit_days: str = "日",
    unit_hours: str = "时",
    unit_minutes: str = "分",
    unit_seconds: str = "秒",
):
    """
    将秒数转换为时间文本

    :param seconds: 要转换的秒数
    :param unit_days: 天的单位
    :param unit_hours: 小时的单位
    :param unit_minutes: 分钟的单位
    :param unit_seconds: 秒的单位
    :return: 转换后的时间文本
    """
    return "{dt}{ld} {ht}{lh} {mt}{lm} {st}{ls}".format(
        dt=seconds // 86400,
        ld=unit_days,
        ht=(seconds % 86400) // 3600,
        lh=unit_hours,
        mt=(seconds % 3600) // 60,
        lm=unit_minutes,
        st=seconds % 60,
        ls=unit_seconds,
    )
