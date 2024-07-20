import os.path

# import time
from os import getcwd

import aiofiles
import nonebot

from nonebot_plugin_htmlrender import * # type: ignore
from .tools import random_hex_string

# import imgkit
# from typing import Any, Dict, Literal, Optional, Union
# import uuid

# import jinja2
# from pathlib import Path

# TEMPLATES_PATH = str(Path(__file__).parent / "templates")
# env = jinja2.Environment(  # noqa: S701
#     extensions=["jinja2.ext.loopcontrols"],
#     loader=jinja2.FileSystemLoader(TEMPLATES_PATH),
#     enable_async=True,
# )


# async def template_to_html(
#     template_path: str,
#     template_name: str,
#     **kwargs,
# ) -> str:
#     """使用jinja2模板引擎通过html生成图片

#     Args:
#         template_path (str): 模板路径
#         template_name (str): 模板名
#         **kwargs: 模板内容
#     Returns:
#         str: html
#     """

#     template_env = jinja2.Environment(  # noqa: S701
#         loader=jinja2.FileSystemLoader(template_path),
#         enable_async=True,
#     )
#     template = template_env.get_template(template_name)

#     return await template.render_async(**kwargs)


# async def template_to_pic(
#     template_path: str,
#     template_name: str,
#     templates: Dict[Any, Any],
#     pages: Optional[Dict[Any, Any]] = None,
#     wait: int = 0,
#     type: Literal["jpeg", "png"] = "png",  # noqa: A002
#     quality: Union[int, None] = None,
#     device_scale_factor: float = 2,
# ) -> bytes:
#     """使用jinja2模板引擎通过html生成图片

#     Args:
#         template_path (str): 模板路径
#         template_name (str): 模板名
#         templates (Dict[Any, Any]): 模板内参数 如: {"name": "abc"}
#         pages (Optional[Dict[Any, Any]]): 网页参数 Defaults to
#             {"base_url": f"file://{getcwd()}", "viewport": {"width": 500, "height": 10}}
#         wait (int, optional): 网页载入等待时间. Defaults to 0.
#         type (Literal["jpeg", "png"]): 图片类型, 默认 png
#         quality (int, optional): 图片质量 0-100 当为`png`时无效
#         device_scale_factor: 缩放比例,类型为float,值越大越清晰(真正想让图片清晰更优先请调整此选项)
#     Returns:
#         bytes: 图片 可直接发送
#     """
#     if pages is None:
#         pages = {
#             "viewport": {"width": 500, "height": 10},
#             "base_url": f"file://{getcwd()}",  # noqa: PTH109
#         }

#     template_env = jinja2.Environment(  # noqa: S701
#         loader=jinja2.FileSystemLoader(template_path),
#         enable_async=True,
#     )
#     template = template_env.get_template(template_name)

#     open(
#         filename := os.path.join(
#             template_path,
#             str(uuid.uuid4())+".html",
#         ),
#         "w",
#     ).write(await template.render_async(**templates))

#     print(pages,filename)


#     img = imgkit.from_file(
#         filename,
#         output_path=False,
#         options={
#             "format": type,
#             "quality": quality if (quality and type == "jpeg") else 94,
#             "allow": pages["base_url"],
#             # "viewport-size": "{} {}".format(pages["viewport"]["width"],pages["viewport"]["height"]),
#             "zoom": device_scale_factor,
#             # "load-error-handling": "ignore",
#             "enable-local-file-access": None,
#             "no-stop-slow-scripts": None,
#             "transparent": None,
#         },
#     )  # type: ignore


#     # os.remove(filename)

#     return img

#     return await html_to_pic(
#         template_path=f"file://{template_path}",
#         html=await template.render_async(**templates),
#         wait=wait,
#         type=type,
#         quality=quality,
#         device_scale_factor=device_scale_factor,
#         **pages,
#     )


async def html2image(
    html: str,
    wait: int = 0,
):
    pass


async def template2html(
    template: str,
    templates: dict,
) -> str:
    """
    Args:
        template: str: 模板文件
        **templates: dict: 模板参数
    Returns:
        HTML 正文
    """
    template_path = os.path.dirname(template)
    template_name = os.path.basename(template)
    return await template_to_html(template_path, template_name, **templates)


async def template2image(
    template: str,
    templates: dict,
    pages=None,
    wait: int = 0,
    scale_factor: float = 1,
    debug: bool = False,
) -> bytes:
    """
    template -> html -> image
    Args:
        debug: 输入渲染好的 html
        wait: 等待时间，单位秒
        pages: 页面参数
        template: str: 模板文件
        templates: dict: 模板参数
        scale_factor: 缩放因子，越高越清晰
    Returns:
        图片二进制数据
    """
    if pages is None:
        pages = {
            "viewport": {"width": 1080, "height": 10},
            "base_url": f"file://{getcwd()}",
        }
    template_path = os.path.dirname(template)
    template_name = os.path.basename(template)

    if debug:
        # 重载资源
        raw_html = await template_to_html(
            template_name=template_name,
            template_path=template_path,
            **templates,
        )
        random_file_name = f"debug-{random_hex_string(6)}.html"
        async with aiofiles.open(
            os.path.join(template_path, random_file_name), "w", encoding="utf-8"
        ) as f:
            await f.write(raw_html)
        nonebot.logger.info("Debug HTML: %s" % f"{random_file_name}")

    return await template_to_pic(
        template_name=template_name,
        template_path=template_path,
        templates=templates,
        pages=pages,
        wait=wait,
        device_scale_factor=scale_factor,
    )


# async def url2image(
#         url: str,
#         wait: int = 0,
#         scale_factor: float = 1,
#         type: str = "png",
#         quality: int = 100,
#         **kwargs
# ) -> bytes:
#     """
#     Args:
#         quality:
#         type:
#         url: str: URL
#         wait: int: 等待时间
#         scale_factor: float: 缩放因子
#         **kwargs: page 参数
#     Returns:
#         图片二进制数据
#     """
#     async with get_new_page(scale_factor) as page:
#         await page.goto(url)
#         await page.wait_for_timeout(wait)
#         return await page.screenshot(
#             full_page=True,
#             type=type,
#             quality=quality
#         )
