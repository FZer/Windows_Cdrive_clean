# core/folder_scanner.py
import os
from utils.convert_size import convert_size
from utils.path_utils import is_junction_point
from config.config import DISPLAY_FOLDER_COUNT


def calculate_folder_size(folder_path):
    """计算文件夹的总大小"""
    total_size = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            try:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
            except Exception as e:
                print(f"Error getting size for {file_path}: {e}")
    return total_size


def collect_folder_information(base_path):
    """收集指定路径下所有文件夹的大小和链接状态信息"""
    print(f"Scanning files in folder: {base_path} ...")
    folders = []

    # 遍历文件夹下的一级项目
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            folder_size = calculate_folder_size(item_path)
            is_junction = is_junction_point(item_path)
            folders.append((item_path, folder_size, is_junction))

    # 按文件夹大小排序（从大到小）
    folders.sort(key=lambda x: x[1], reverse=True)
    if not folders:
        raise Exception(f"在路径'{base_path}'中没有找到任何文件夹!")
    return folders


def display_largest_folders(folder_list: list, display_count: int = DISPLAY_FOLDER_COUNT):
    """打印最大的指定数量的文件夹信息"""
    print(f"\n=============前{display_count}个最大的文件夹=============")

    # 限制显示的文件夹数量
    folders = folder_list[:display_count]
    for i, (folder_path, folder_size, is_junction) in enumerate(folders, 1):
        junction_status = "[已转移] " if is_junction else ""
        print(
            f"{i}. {folder_path}: {convert_size(folder_size)}------->{junction_status}")
    return folders
