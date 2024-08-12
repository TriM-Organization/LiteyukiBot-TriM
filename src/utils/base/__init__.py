import threading

from nonebot import logger
from liteyuki.comm.channel import get_channel


def reload(delay: float = 0.0, receiver: str = "nonebot"):
    """
    重载LiteyukiBot(nonebot)
    Args:
        receiver: 指定重载的进程
        delay:

    Returns:

    """
    chan = get_channel(receiver + "-active")
    if chan is None:
        logger.error(f"未见 Channel {receiver}-active 以至无法重载")
        return

    if delay > 0:
        threading.Timer(delay, chan.send, args=(1,)).start()
        return
    else:
        chan.send(1)
