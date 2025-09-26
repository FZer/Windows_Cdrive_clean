# main.py
import os
import ctypes
from utils.path_utils import get_roaming_folder, get_temp_folder, get_documents_folder, is_junction_point
from core.folder_scanner import collect_folder_information, display_largest_folders
from ui.user_interface import get_user_choice
from core.folder_manager import prepare_destination_path, perform_copy_operation
from core.folder_scanner import calculate_folder_size
from utils.convert_size import convert_size


def copy_selected_folder(folders: list):
    """复制选定的文件夹到隐藏目录中"""
    try:
        # 获取用户选择并验证
        selected_folder_path, selected_folder_name = get_user_choice(folders)
        if selected_folder_path is None or selected_folder_name is None:
            return
        selected_folder_size = None
        for folder_path, folder_size, is_junction in folders:
            if folder_path == selected_folder_path:
                selected_folder_size = folder_size
                break
        # 准备目标路径
        dest_folder_path = prepare_destination_path(
            selected_folder_name, selected_folder_size)
        if dest_folder_path is None:
            return
        # 执行复制操作
        perform_copy_operation(selected_folder_path,
                               dest_folder_path, selected_folder_name)
    except Exception as e:
        print("function of copy_selected_folder is error: ", e)


def delete_temp_files():
    """删除当前用户的临时文件夹中的所有内容"""
    try:
        temp_path = get_temp_folder()
        before_size = calculate_folder_size(temp_path)
        print(f"临时文件夹{temp_path}占用空间: {convert_size(before_size)}")
        start = input("确认删除临时文件夹中的所有内容？(Y/N): ").strip().lower()
        if start != 'y':
            print("已取消删除操作")
            return
        print(f"正在删除临时文件夹中的内容,请稍候...")
        # 遍历临时文件夹中的所有文件和子文件夹
        for root, dirs, files in os.walk(temp_path, topdown=False):
            # 先删除文件
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"已删除文件: {file_path}")
                except Exception as e:
                    # print(f"无法删除文件 {file_path}: {e}")
                    continue

            # 再删除文件夹
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                    # print(f"已删除文件夹: {dir_path}")
                except Exception as e:
                    # print(f"无法删除文件夹 {dir_path}: {e}")
                    continue
        after_size = calculate_folder_size(temp_path)
        freed_space = before_size - after_size
        print(
            f"临时文件夹内容清理完成，释放空间: {convert_size(freed_space)},当前占用空间: {convert_size(after_size)}")
    except Exception as e:
        print(f"清理临时文件夹时出错: {e}")


def transfer_documents():
    """转移文档文件夹到其他磁盘并创建软链接"""
    try:
        # 获取文档文件夹路径
        docs_path = get_documents_folder()
        docs_name = os.path.basename(docs_path)
        if is_junction_point(docs_path):
            print(f"文件夹{docs_path}已创建链接，请重新选择!\n")
            return

        # 计算文档文件夹大小（使用已有的函数）
        total_size = calculate_folder_size(docs_path)

        # 准备目标路径（使用已有的函数）
        dest_folder_path = prepare_destination_path(
            docs_name, total_size)
        if dest_folder_path is None:
            return
        # 执行复制操作（使用已有的函数）
        perform_copy_operation(docs_path, dest_folder_path, docs_name)
    except Exception as e:
        print(f"转移文档文件夹时出错: {e}\n")


def transfer_app_data():
    """转移应用数据（原有的程序功能）"""
    try:
        # 获取Roaming文件夹路径
        roaming_path = get_roaming_folder()

        # 收集并处理文件夹信息并排序
        folders = collect_folder_information(roaming_path)

        # 打印最大的20个文件夹信息
        folders = display_largest_folders(folders)

        # 调用复制函数，让用户选择需要复制的文件夹
        copy_selected_folder(folders)
    except Exception as e:
        print(f"转移应用数据时出错: {e}")


def main():
    """主函数，提供菜单选择"""
    print("\n===================C盘清理工具===================")
    print("Version: 1.1.0")
    print("Author: FZ")
    print("==================================================\n")
    print("开始清理前，请尽可能的退出程序和关掉窗口，或进行1次登录注销后再运行该程序\n")

    kill_user = input("(已经注销过则跳过该步骤)确定要注销当前登录吗？(Y/N): ").strip().lower()
    if kill_user == 'y':
        ctypes.windll.user32.ExitWindowsEx(0, 0)
    print("===================================================")
    while True:
        print("")
        print("1. 删除系统盘临时文件")
        print("2. 转移文档数据")
        print("3. 转移应用数据")
        choice = input("\n请选择要执行操作的对应的序号,或输入'q'退出,回车键确认:").strip().lower()
        if choice == '1':
            delete_temp_files()
        elif choice == '2':
            transfer_documents()
        elif choice == '3':
            transfer_app_data()
        elif choice == 'q':
            print("程序已退出。")
            break
        else:
            print("无效的选项，请重新输入。")


if __name__ == "__main__":
    main()
