# ui/user_interface.py
import os
import time
import shutil
from config.config import RETRY_DELAY, MAX_RETRIES, DISPLAY_FOLDER_COUNT
from core.process_manager import all_kill_process


def get_user_choice(folders):
    """获取并返回用户选择的文件夹序号"""
    while True:
        try:
            choice = input(
                f"\n输入需要复制的文件夹前的序号(1-{DISPLAY_FOLDER_COUNT}),或输入'q'退出,回车键确认: ")
            if choice == 'q':
                print("程序已退出!")
                return None, None
            if choice.isdigit() == False:
                continue
            choice = int(choice)
            if choice in range(1, DISPLAY_FOLDER_COUNT + 1):
                # 判断用户选择的序号，如果已经创建了软链接，则提示用户重新选择
                if folders[choice - 1][2] == True:
                    print(f"文件夹 {folders[choice - 1][0]} 已创建链接，请重新选择。")
                    continue
                selected_folder_path = folders[choice - 1][0]
                selected_folder_name = os.path.basename(selected_folder_path)
                return selected_folder_path, selected_folder_name
        except Exception as e:
            print(f"function of get_user_choice is error: {e}")


def delete_file_or_folder(path):
    """专门处理文件或文件夹删除操作，使用ignore_errors=True删除，然后处理残留文件"""
    success = False
    from core.folder_manager import _modify_permissions_recursive
    # 检查路径是否为目录
    if not os.path.isdir(path):
        print(f"参数必须是目录地址: {path}")
        return False
    _modify_permissions_recursive(path)
    # 尝试删除目录，最多重试MAX_RETRIES次
    del_count = 0
    print(f"=========开始删除目录{path}==========\n")
    while os.path.exists(path) and del_count < MAX_RETRIES:
        del_count += 1
        # 使用ignore_errors=True删除目录
        print(f"开始第{del_count}次删除目录{path}...")
        shutil.rmtree(path, ignore_errors=True)
        # 检查目录是否仍存在
        time.sleep(RETRY_DELAY)
        if os.path.exists(path):
            # 提取所有残留文件的路径
            failed_files = []
            try:
                # 递归遍历残留目录，收集所有文件路径
                for root, _, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        failed_files.append(file_path)
                if failed_files:
                    print(f"发现 {len(failed_files)} 个无法删除的文件")
                    # 调用修改后的find_file_process函数，传入文件列表
                    all_kill_process(failed_files)
                else:
                    print(f"文件夹{path}中已经没有残留文件，但是该文件夹无法自动删除，请手动删除。\n")
                    while True:
                        user_input = input(f"确认手动删除了文件夹{path}后，请输入YES:")
                        if user_input == "YES":
                            break
            except Exception as e:
                print(f"扫描残留文件时发生错误: {str(e)}")
    time.sleep(RETRY_DELAY)
    if os.path.exists(path):
        print(f"目录 {path} 删除失败")
        return success
    else:
        print(f"目录 {path} 已成功删除")
        success = True
        return success


def confirm_overwrite(folder_path):
    """询问用户是否确认覆盖已存在的文件夹"""
    print(f"文件夹 {folder_path} 已存在。")
    confirm = input("\n是否删除现有文件夹并继续复制? (Y/N): ").strip().lower()
    if confirm == 'y':
        # 使用新的删除函数删除已存在的文件夹
        if os.path.exists(folder_path):
            success = delete_file_or_folder(folder_path)
            if not success:
                print("复制操作已取消。\n")
                return False
        return True
    else:
        print("复制操作已取消。\n")
        return False


def confirm_kill_process():
    """询问用户是否确认终止占用进程"""
    return input("\n是否要终止相关进程，然后重新尝试? (Y/N): ").strip().lower() == 'y'


def re_copy_failed_files(failed_files, src_folder, dest_folder):
    """处理复制失败的文件，调用find_file_process查找并终止占用进程，然后重新复制所有文件"""
    retry_success_count = 0

    if not failed_files:
        return retry_success_count

    all_kill_process(failed_files)

    # 尝试重新复制所有失败的文件
    print("\n===== 开始重新复制所有失败的文件 =====")
    for src, error in failed_files:
        if os.path.exists(src):
            print(f"尝试重新复制文件: {src}")
            if retry_copy_file(src, src_folder, dest_folder):
                retry_success_count += 1

    return retry_success_count


def retry_copy_file(src, src_folder, dest_folder):
    """尝试多次复制文件，返回是否成功"""
    import shutil
    retry_count = 0
    success = False

    while retry_count < MAX_RETRIES and not success:
        try:
            dst_path = os.path.join(
                dest_folder, os.path.relpath(src, src_folder)
            )
            print(f"--------尝试复制--------: {src}\n")
            dst_path_dir = os.path.dirname(dst_path)
            shutil.copy2(src, dst_path_dir)
            print(f"成功重新复制文件: {src}")
            success = True
        except Exception as e:
            retry_count += 1
            print(f"重新复制文件失败 (重试 {retry_count}/{MAX_RETRIES}): {e}")
            if retry_count < MAX_RETRIES:
                print(f"等待{RETRY_DELAY}秒后重试...")
                time.sleep(RETRY_DELAY)

    return success


def show_copy_results(copied, retry_success_count, failed_folders, src_folder, dest_folder):
    """显示复制操作的最终结果"""
    from core.folder_manager import create_directory_junction
    total_success = copied + retry_success_count
    print(f"\n=============复制完成=============")
    if retry_success_count > 0:
        print(
            f"总共复制成功 {total_success} 个文件，包含重新复制成功的 {retry_success_count} 个文件.")
    else:
        print(f"总共复制成功 {total_success} 个文件.")

    if failed_folders:
        print(f"{len(failed_folders)} 个文件夹复制并创建失败:")
        for src, error in failed_folders:
            print(f"{src}: {error}")
    else:
        print("所有文件夹创建成功!\n")
        create_directory_junction(src_folder, dest_folder)
