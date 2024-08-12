import nonebot
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from liteyuki.bot import get_bot
from src.utils.base import reload
from src.utils.base.config import get_config
from src.utils.base.resource import load_resources

if get_config("debug", False):

    liteyuki_bot = get_bot()

    res_directories = (
        "src/resources",
        "resources",
    )

    class ResourceModifiedHandler(FileSystemEventHandler):
        """
        Handler for resource file changes
        """

        def on_modified(self, event):
            nonebot.logger.info(f"资源 {event.src_path} 变更，重载资源包……")
            load_resources()

    resource_modified_handle = ResourceModifiedHandler()

    observer = Observer()
    for directory in res_directories:
        observer.schedule(resource_modified_handle, directory, recursive=True)
    observer.start()
