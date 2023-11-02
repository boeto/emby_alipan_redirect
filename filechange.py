import logging
import os
import shutil
from pathlib import Path
from typing import Any

import yaml

from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver
from watchdog.observers import Observer

# import aliyunpan

logging.basicConfig(
    filename="alipan_redirect",
    format="%(asctime)s - %(name)s - %(levelname)s -%(module)s:  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S ",
    level=logging.INFO,
)
logger = logging.getLogger()
KZT = logging.StreamHandler()
KZT.setLevel(logging.DEBUG)
logger.addHandler(KZT)


def delete_empty_parent_directory(file_path):
    parent_dir = Path(file_path).parent
    if (
        parent_dir != Path("/")
        and parent_dir.is_dir()
        and not any(parent_dir.iterdir())
        and parent_dir.exists()
    ):
        try:
            parent_dir.rmdir()
            logger.info(f"删除空的父文件夹: {parent_dir}")
        except OSError as e:
            logger.error(f"删除空父目录失败: {e}")


class FileMonitorHandler(FileSystemEventHandler):
    """
    目录监控响应类
    """

    def __init__(
        self,
        watching_path: str,
        file_change: Any,
        **kwargs,
    ):
        super(FileMonitorHandler, self).__init__(**kwargs)
        self.watching_path = watching_path
        self.file_change = file_change

    def on_any_event(self, event):
        logger.info(f"目录监控event_type::: {event.event_type}")
        logger.info(f"目录监控on_any_event事件路径::: {event.src_path}")

    def on_created(self, event):
        logger.info(f"目录监控created事件路径::: {event.src_path}")
        self.file_change.event_handler(event=event, event_path=event.src_path)

    def on_deleted(self, event):
        logger.info(f"目录监控deleted事件路径 src_path::: {event.src_path}")
        self.file_change.event_handler(event=event, event_path=event.src_path)

    def on_moved(self, event):
        logger.info(f"目录监控moved事件路径 src_path::: {event.src_path}")
        logger.info(f"目录监控moved事件路径 dest_path::: {event.dest_path}")
        logger.info("fast模式能触发，暂不处理")
        # self.sync.event_handler(event=event, event_path=event.dest_path)


class FileChange:
    def __init__(self):
        # self.alipan = aliyunpan.AliyunPan()

        filepath = os.path.join("/mnt", "config.yaml")
        with open(filepath, "r") as f:  # 用with读取文件更好
            self.configs = yaml.load(f, Loader=yaml.FullLoader)  # 按字典格式读取并返回

        # self.dav_directory = str(self.configs["sync"]["dav_directory"])

        # # 监控哪个文件夹
        # self.dav_watching_directory = self.dav_directory + str(
        #     self.configs["sync"]["dav_source_directory"]
        # )
        self.monitoring_directory = str(
            self.configs["sync"]["monitoring_directory"]
        )

        # drives数组，暂无功能，预留对不同的平台进行不同的处理
        self.drives_list = str(self.configs["sync"]["drives"]).split(",")

        # strm文件存储路径
        self.destination_directory = str(
            self.configs["sync"]["destination_directory"]
        )

        # strm播放路径
        self.emby_directory = str(self.configs["sync"]["emby_directory"])

        self.monitoring_mode = str(self.configs["sync"]["monitoring_mode"])

    def create_strm_file(
        self,
        dest_file: str,
    ):
        try:
            # 获取视频文件名和目录
            video_name = Path(dest_file).name

            dest_path = Path(dest_file).parent

            if not dest_path.exists():
                logger.info(f"创建目标文件夹 {dest_path}")
                os.makedirs(str(dest_path))

            # 构造.strm文件路径
            strm_path = os.path.join(
                dest_path, f"{os.path.splitext(video_name)[0]}.strm"
            )

            logger.info(f"dest_dir1:::{dest_file}")
            # 本地挂载路径转为emby路径
            dest_file = dest_file.replace(
                self.destination_directory, self.emby_directory
            )
            logger.info(f"dest_dir2:::{dest_file}")

            # 写入.strm文件
            with open(strm_path, "w") as f:
                f.write(dest_file)

            logger.info(f"创建strm文件 {strm_path}")

            # 获取阿里云盘file_id，存储
            # self.alipan.save_new_file_id(dest_dir=dest_file)
        except Exception as e:
            print(str(e))

    def start(self):
        if self.monitoring_mode == "compatibility":
            # 兼容模式，目录同步性能降低且NAS不能休眠，但可以兼容挂载的远程共享目录如SMB
            observer = PollingObserver(timeout=10)

        else:
            # 内部处理系统操作类型选择最优解
            observer = Observer(timeout=10)

        # 监控哪个文件夹
        observer.schedule(
            FileMonitorHandler(self.monitoring_directory, self),
            path=self.monitoring_directory,
            recursive=True,
        )
        logger.info(f"监控模式为::: {self.monitoring_mode}")
        logger.info(f"开始监控文件夹 {self.monitoring_directory}")
        observer.daemon = True
        observer.start()

    def event_handler(self, event, event_path: str):
        # 回收站及隐藏的文件不处理
        if (
            event_path.find("/@Recycle") != -1
            or event_path.find("/#recycle") != -1
            or event_path.find("/.") != -1
            or event_path.find("/@eaDir") != -1
        ):
            logger.info(f"{event_path} 是回收站或隐藏的文件，跳过处理")
            return

        logger.info(f"event_type::: {event.event_type}")

        if event.event_type == "created":
            self.event_handler_created(event, event_path)
        if event.event_type == "deleted":
            self.event_handler_deleted(event_path)

    def event_handler_created(
        self,
        event,
        event_path: str,
    ):
        try:
            logger.info(f"event_handler_created event_path:::{event_path}")
            # 文件夹同步创建
            if event.is_directory:
                target_path = event_path.replace(
                    self.monitoring_directory,
                    self.destination_directory,
                )
                # 目标文件夹不存在则创建
                if not Path(target_path).exists():
                    logger.info(f"创建目标文件夹 {target_path}")
                    os.makedirs(target_path)

            else:
                # 文件：nfo、图片、视频文件
                dest_file = event_path.replace(
                    self.monitoring_directory,
                    self.destination_directory,
                )

                if Path(dest_file).exists():
                    logger.info(f"目标文件已存在,跳过处理::: {dest_file} ")
                    # continue

                # 目标文件夹不存在则创建
                if not Path(dest_file).parent.exists():
                    logger.info(f"创建目标文件夹 {Path(dest_file).parent}")
                    os.makedirs(Path(dest_file).parent)

                # 视频文件创建.strm文件
                video_formats = (
                    ".mp4",
                    ".avi",
                    ".rmvb",
                    ".wmv",
                    ".mov",
                    ".mkv",
                    ".flv",
                    ".ts",
                    ".webm",
                    ".iso",
                    ".mpg",
                )

                if event_path.lower().endswith(video_formats):
                    # 如果视频文件小于1MB，则直接复制，不创建.strm文件
                    if os.path.getsize(event_path) < 1024 * 1024:
                        shutil.copy2(event_path, dest_file)
                        logger.info(f"复制视频文件 {event_path} 到 {dest_file}")

                        # 本地挂载路径转为emby路径
                        # dest_dir = dest_file.replace(
                        #     destination_directory,
                        #     self.emby_directory,
                        # )
                        # 获取阿里云盘file_id，存储
                        # self.alipan.save_new_file_id(dest_dir=dest_dir)
                    else:
                        # 创建.strm文件
                        self.create_strm_file(dest_file)
                else:
                    # 其他nfo、jpg等复制文件
                    shutil.copy2(event_path, dest_file)
                    logger.info(f"复制非视频文件 {event_path} 到 {dest_file}")

        except Exception as e:
            logger.error(f"event_handler_created error: {e}")
            print(str(e))

    def event_handler_deleted(
        self,
        event_path: str,
    ):
        deleted_target_path = event_path.replace(
            self.monitoring_directory,
            self.destination_directory,
        )

        # 只删除不存在的目标路径
        if not Path(deleted_target_path).exists():
            logger.info(f"目标路径不存在，跳过删除::: {deleted_target_path}")
        else:
            logger.info(f"目标路径存在，删除::: {deleted_target_path}")

            if Path(deleted_target_path).is_file():
                Path(deleted_target_path).unlink()
            else:
                # 非根目录，才删除目录
                shutil.rmtree(deleted_target_path)
        delete_empty_parent_directory(event_path)
