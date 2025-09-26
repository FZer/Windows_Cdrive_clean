# utils/path_utils.py
import os
import ctypes


def get_roaming_folder():
    """获取 Roaming 文件夹的路径"""
    roaming_path = os.path.join(os.environ['APPDATA'])
    return roaming_path


def get_temp_folder():
    """获取用户临时文件夹的路径"""
    temp_path = os.path.join(os.environ['TEMP'])
    return temp_path


def get_documents_folder():
    """获取用户文档文件夹的路径"""
    # 在Windows中，使用USERPROFILE环境变量拼接Documents路径
    docs_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
    return docs_path


def is_junction_point(path):
    """检查路径是否是通过 mklink /J 创建的目录链接（Junction Point）"""
    if not os.path.isdir(path):
        return False
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    GetFileAttributesW = ctypes.windll.kernel32.GetFileAttributesW
    attributes = GetFileAttributesW(path)
    return (attributes & FILE_ATTRIBUTE_REPARSE_POINT) != 0
