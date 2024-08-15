import zhDateTime


def utime_hanzify(
    zhd: zhDateTime.zhDateTime = zhDateTime.DateTime.now().to_lunar(),
) -> str:
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