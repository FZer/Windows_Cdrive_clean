# config.py
HIDDEN_FOLDER_NAME = "AppData"   # 创建的隐藏文件夹的名称
ROAMING_FOLDER_NAME = "Roaming"  # 要扫描的文件夹的名称
MAX_RETRIES = 10  # 删除或复制失败后的最大重试次数
RETRY_DELAY = 2  # 等待时间(秒)
DISPLAY_FOLDER_COUNT = 10  # 要显示的最大文件夹排序的数量

__all__ = [
    'HIDDEN_FOLDER_NAME',
    'ROAMING_FOLDER_NAME',
    'MAX_RETRIES',
    'RETRY_DELAY',
    'DISPLAY_FOLDER_COUNT'
]
