import zhDateTime
from typing import Optional



def hanzi_timeid(
    zhd: Optional[zhDateTime.zhDateTime] = None,
) -> str:
    if not zhd:
        zhd = zhDateTime.DateTime.now().to_lunar()
    
    return "{地支时}{刻}{分}{秒}".format(
        地支时=zhDateTime.DÌZHĪ[zhd.shichen]
        + (
            ""
            if ((zhd.quarters) or (zhd.minutes) or (zhd.seconds) or (zhd.microseconds))
            else "整"
        ),
        刻=(
            (zhDateTime.HANNUM[zhd.quarters])
            + ("" if ((zhd.minutes) or (zhd.seconds) or (zhd.microseconds)) else "整")
        ),
        分=(
            zhDateTime.lkint_hànzìfy(zhd.minutes)
            + ("" if ((zhd.seconds) or (zhd.microseconds)) else "整")
        ),
        秒=(
            zhDateTime.HANNUM[zhd.seconds // 10]
            + zhDateTime.HANNUM[zhd.seconds % 10]
            + ("" if (zhd.microseconds) else "整")
        ),
    ).strip()



# def isin(sth: str, range_list: dict):
#     sth = sth.lower()
#     for bool_value, res_list in range_list.items():
#         if sth in res_list:
#             return bool_value
#     raise ValueError(
#         "不在可选范围内：{}".format([j for i in range_list.values() for j in i])
#     )


# # 真假字符串判断
# def bool_str(sth: str):
#     try:
#         return bool(float(sth))
#     except ValueError:
#         if str(sth).lower() in ("true", "真", "是", "y", "t"):
#             return True
#         elif str(sth).lower() in ("false", "假", "否", "f", "n"):
#             return False
#         else:
#             raise ValueError("非法逻辑字串")


# def float_str(sth: str):
#     try:
#         return float(sth)
#     except ValueError:
#         return float(
#             sth.replace("壹", "1")
#             .replace("贰", "2")
#             .replace("叁", "3")
#             .replace("肆", "4")
#             .replace("伍", "5")
#             .replace("陆", "6")
#             .replace("柒", "7")
#             .replace("捌", "8")
#             .replace("玖", "9")
#             .replace("零", "0")
#             .replace("一", "1")
#             .replace("二", "2")
#             .replace("三", "3")
#             .replace("四", "4")
#             .replace("五", "5")
#             .replace("六", "6")
#             .replace("七", "7")
#             .replace("八", "8")
#             .replace("九", "9")
#             .replace("〇", "0")
#             .replace("洞", "0")
#             .replace("幺", "1")
#             .replace("俩", "2")
#             .replace("两", "2")
#             .replace("拐", "7")
#             .replace("点", ".")
#         )


# def int_str(sth: str):
#     return int(float_str(sth))
