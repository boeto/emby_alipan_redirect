import os
import shutil

import yaml
import logging

# import urllib.parse
from pathlib import Path

logger = logging.getLogger()


def create_strm_file(dest_file, destination, emby_directory):
    # 获取视频文件名和目录
    video_name = Path(dest_file).name

    dest_path = Path(dest_file).parent

    # 构造.strm文件路径
    strm_path = os.path.join(
        dest_path, f"{os.path.splitext(video_name)[0]}.strm"
    )

    if os.path.exists(strm_path):
        print(f"strm文件已存在，跳过处理::: {strm_path}")
        return

    # 本地挂载路径转为emby路径
    emby_play_path = dest_file.replace(destination, emby_directory)

    print(f"dest_file 处理文件::: {dest_file}")
    print(f"video_name 文件名字::: {video_name}")
    print(f"dest_path parent 文件目录::: {dest_path}")
    print(f"strm_path strm路径::: {strm_path}")
    print(f"emby_play_path emby播放地址::: {emby_play_path}")

    # 写入.strm文件
    with open(strm_path, "w") as f:
        f.write(emby_play_path)

    print(f"已写入 {strm_path}::: {emby_play_path}")


def copy_files(source, destination, emby_directory):
    if not os.path.exists(destination):
        os.makedirs(destination)

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

    for root, dirs, files in os.walk(source):
        # 如果遇到名为'extrafanart'的文件夹，则跳过处理该文件夹，继续处理其他文件夹
        if "extrafanart" in dirs:
            dirs.remove("extrafanart")

        for file in files:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(
                destination, os.path.relpath(source_file, source)
            )
            dest_dir = os.path.dirname(dest_file)

            print("=================================================")
            print(f"处理文件::: {dest_file}")

            # 创建目标目录中缺少的文件夹
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            # 如果目标文件已存在，跳过处理
            if os.path.exists(dest_file):
                print(f"文件已存在，跳过处理::: {dest_file}")
                continue

            # 如果遇到名为'trailers'的文件夹
            # if os.path.basename(root) == "trailers":
            #     backdrops_dir = os.path.join(
            #         os.path.dirname(dest_dir), "backdrops"
            #     )
            #     if not os.path.exists(backdrops_dir):
            #         os.makedirs(backdrops_dir)
            #     create_strm_file(backdrops_dir, destination, emby_directory)

            #     trailers_dir = os.path.join(
            #         os.path.dirname(dest_dir), "trailers"
            #     )
            #     if not os.path.exists(trailers_dir):
            #         os.makedirs(trailers_dir)
            #     create_strm_file(trailers_dir, destination, emby_directory)
            # else:

            if file.lower().endswith(video_formats):
                # 如果视频文件小于1MB，则直接复制，不创建.strm文件
                if os.path.getsize(source_file) < 1024 * 1024:
                    print(f"视频文件小于1MB的视频文件到:::{dest_file}")
                    shutil.copy2(source_file, dest_file)
                else:
                    # 创建.strm文件
                    create_strm_file(dest_file, destination, emby_directory)
                    # create_strm_file(dest_dir, destination, emby_directory)
            else:
                # 复制文件
                print(f"复制其他文件到:::{dest_file}")
                shutil.copy2(source_file, dest_file)


# 指定目录a和目录b的路径
# source_directory = "/mnt/user/downloads/CloudDrive/aliyun/emby"
# destination_directory = "/mnt/user/downloads/link/aliyun"
# emby_directory = "/data/aliyun"

filepath = os.path.join("/mnt", "config.yaml")

with open(filepath, "r") as f:  # 用with读取文件更好
    configs = yaml.load(f, Loader=yaml.FullLoader)  # 按字典格式读取并返回

# dav_directory = str(configs["sync"]["dav_directory"])
# dav_source_directory = dav_directory + str(
#     configs["sync"]["dav_source_directory"]
# )
monitoring_directory = str(configs["sync"]["monitoring_directory"])
destination_directory = str(configs["sync"]["destination_directory"])

emby_directory = str(configs["sync"]["emby_directory"])

print(f"monitoring_directory::: {monitoring_directory}")
print(f"emby_directory::: {emby_directory}")

print(f"开始遍历复制文件 {monitoring_directory}")

copy_files(monitoring_directory, destination_directory, emby_directory)

print("遍历复制文件完成")
