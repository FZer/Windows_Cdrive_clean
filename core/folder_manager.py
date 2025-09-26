# core/folder_manager.py
import os
import shutil
import ctypes
import subprocess
import tqdm
import stat
from config.config import HIDDEN_FOLDER_NAME, ROAMING_FOLDER_NAME
from ui.user_interface import delete_file_or_folder


def copy_with_progress(src, dst):
    """使用 tqdm 显示复制进度"""
    total_files = sum(len(files) for _, _, files in os.walk(src))
    copied_files = 0
    failed_files = []
    # 然后确保所有空文件夹也被创建
    empty_folders = []
    # 修改文件权限
    if os.path.isfile(src):
        # 获取文件所在目录
        folder_path = os.path.dirname(src)
        _modify_permissions_recursive(folder_path)
    else:
        _modify_permissions_recursive(src)
    # 首先复制文件
    with tqdm.tqdm(total=total_files, unit='file', desc='Copying files') as pbar:
        for root, dirs, files in os.walk(src):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, src)
                dst_path = os.path.join(dst, rel_path)
                try:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    pbar.update(1)
                    copied_files += 1
                except Exception as e:
                    failed_files.append((src_path, str(e)))
                    # 打印错误信息
                    pbar.write(f"\n文件复制过程中出现错误: {e}")
                    pbar.write(f"继续复制其它文件...")
    # 遍历所有文件夹，包括空文件夹
    for root, dirs, files in os.walk(src):
        for dir_name in dirs:
            src_dir_path = os.path.join(root, dir_name)
            rel_dir_path = os.path.relpath(src_dir_path, src)
            dst_dir_path = os.path.join(dst, rel_dir_path)
            try:
                os.makedirs(dst_dir_path, exist_ok=True)
            except Exception as e:
                print(f"创建文件夹 {dst_dir_path}时出现错误: {e}")
                empty_folders.append((src_dir_path, str(e)))
    return copied_files, failed_files, empty_folders


def _modify_permissions_recursive(path):
    """
    递归修改指定路径及其所有子项的权限
    """
    try:
        # 修改当前目录或文件的权限
        os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        # 如果是目录，递归修改子项
        if os.path.isdir(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                _modify_permissions_recursive(item_path)
    except Exception as e:
        print(f"修改权限时发生错误: {path}, 错误: {e}")


def create_directory_junction(original_dir, target_dir):
    """创建Windows目录链接(Junction Point)
    在创建链接前删除原目录及其所有内容
    """
    try:
        # 检查原目录是否存在，如果存在则删除
        if os.path.exists(original_dir):
            success = delete_file_or_folder(
                original_dir)
            if success == False:
                return False

        # 执行MKLINK /J命令创建目录链接
        print(f"正在创建链接: {original_dir} -> {target_dir}")
        result = subprocess.run(
            ['mklink', '/J', original_dir, target_dir],
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        print(f"链接创建成功!")
        return True
    # except subprocess.CalledProcessError as e:
    #     print(f"创建链接失败: {e.stderr}")
    #     return False
    except Exception as e:
        print(f"操作失败: {str(e)}")
        return False


def check_disk_space(drive_path, required_space):
    """检查指定磁盘的剩余空间是否足够"""
    try:
        # 获取磁盘使用情况 (Windows系统)
        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(drive_path),
                                                   None,
                                                   ctypes.pointer(total_bytes),
                                                   ctypes.pointer(free_bytes))
        free_space_gb = free_bytes.value / (1024 * 1024 * 1024)
        required_space_gb = required_space / (1024 * 1024 * 1024)

        print(f"磁盘 {drive_path} 剩余空间: {free_space_gb:.2f} GB")
        print(f"复制文件所需空间: {required_space_gb:.2f} GB")

        return free_bytes.value >= required_space
    except Exception as e:
        print(f"检查磁盘空间时出错: {e}")
        return False


def select_destination_drive():
    """让用户选择目标磁盘，不选择默认为第一个除了系统盘的磁盘"""
    windows_dir = os.environ.get('SystemRoot')
    system_drive = windows_dir[:2] if windows_dir else None
    try:
        # 使用更高效的方法获取可用驱动器列表（Windows系统）
        available_drives = []

        # 方法1: 使用subprocess调用wmic命令获取所有逻辑驱动器（更高效）
        try:
            result = subprocess.run(['wmic', 'logicaldisk', 'get', 'caption'],
                                    capture_output=True, text=True, check=True, shell=True)
            # 解析输出，提取驱动器字母
            for line in result.stdout.strip().split('\n')[1:]:  # 跳过标题行
                drive = line.strip()

                if drive:  # 确保不为空
                    if drive == system_drive:  # 跳过系统盘
                        continue
                    drive_path = f"{drive}\\"
                    available_drives.append(drive_path)
        except Exception as e:
            # print(f"使用wmic命令获取驱动器列表失败: {e}")
            # 方法2: 备选方案: 检查所有驱动器字母
            for drive_letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':  # 检查所有驱动器字母
                if drive == system_drive:  # 跳过系统盘
                    continue
                drive_path = f"{drive_letter}:\\"
                if os.path.exists(drive_path) and os.path.isdir(drive_path):
                    available_drives.append(drive_path)
        if not available_drives:
            print("没有找到多余的磁盘驱动器")
            return None
        # 显示可用驱动器列表
        print(f"\n========可用的磁盘驱动器如下========")
        for i, drive in enumerate(available_drives, 1):
            print(f"{i}. {drive}")

        # 询问用户选择，循环直到获得有效输入
        while True:
            choice = input(
                f"\n请输入目标磁盘前的序号(不输入则默认为第1个选项),或输入'q'退出,按回车确认: ").strip()
            print("\n")
            if choice.lower() == 'q':
                print("已退出选择")
                return None
            if choice == "":
                # 如果用户没有输入序号，使用第一个可用磁盘
                return available_drives[0]
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(available_drives):
                    return available_drives[index]
            else:
                continue
    except Exception as e:
        print(f"选择目标磁盘时出错,function of select_destination_drive: {e}")


def prepare_destination_path(selected_folder_name, required_space=None):
    """准备目标路径，创建必要的目录结构"""
    from ui.user_interface import confirm_overwrite
    # 让用户选择目标磁盘
    drive_path = select_destination_drive()

    # 检查用户是否选择了退出
    if drive_path is None:
        return None
    # 检查剩余空间是否足够
    if required_space is not None:
        if not check_disk_space(drive_path, required_space):
            print(f"磁盘 {drive_path} 剩余空间不足，无法完成复制操作。")
            return None

    # 创建隐藏文件夹AppData
    hidden_folder_path = os.path.join(drive_path, HIDDEN_FOLDER_NAME)
    if not os.path.exists(hidden_folder_path):
        os.makedirs(hidden_folder_path)
    # 设置隐藏属性
    ctypes.windll.kernel32.SetFileAttributesW(hidden_folder_path, 2)

    # 创建Roaming文件夹
    roaming_dest_path = os.path.join(hidden_folder_path, ROAMING_FOLDER_NAME)
    if not os.path.exists(roaming_dest_path):
        os.makedirs(roaming_dest_path)

    # 检查目标文件夹是否已经存在,如果存在则询问用户是否覆盖
    dest_folder_path = os.path.join(roaming_dest_path, selected_folder_name)
    if os.path.exists(dest_folder_path):
        if confirm_overwrite(dest_folder_path) == False:
            return None
    return dest_folder_path


def perform_copy_operation(src_folder, dest_folder, folder_name):
    """执行文件夹复制操作并处理可能出现的问题"""
    from ui.user_interface import show_copy_results, re_copy_failed_files
    # 复制选定的文件夹到目标路径
    print(f"正在复制 {folder_name} 到 {os.path.dirname(dest_folder)}...")
    copied, failed_files, failed_folders = copy_with_progress(
        src_folder, dest_folder)

    # 处理复制失败的文件
    retry_success_count = 0
    if failed_files:
        retry_success_count = re_copy_failed_files(
            failed_files, src_folder, dest_folder)

    # 显示复制结果
    show_copy_results(copied, retry_success_count,
                      failed_folders, src_folder, dest_folder)
