# core/process_manager.py
import psutil
import os
import time
from config.config import RETRY_DELAY


def all_kill_process(failed_files: list):
    """
    杀死所有使用指定文件进程
    """
    # 调用find_file_process查找占用指定文件的进程
    process_info_dict = find_file_process(failed_files)

    # 收集所有需要终止的进程ID
    process_ids_to_kill = set()
    for src, process_info in process_info_dict.items():
        for proc in process_info:
            process_ids_to_kill.add(proc['pid'])  # 添加直接占用的进程ID

    # 如果有进程需要终止，一次性终止所有进程
    if process_ids_to_kill:
        from ui.user_interface import confirm_kill_process
        if confirm_kill_process() == True:
            print(f"\n===== 开始终止占用文件的进程 =====")
            print(f"找到 {len(process_ids_to_kill)} 个需要终止的进程ID")

            # 准备进程信息列表
            process_list = []
            for pid in process_ids_to_kill:
                try:
                    proc = psutil.Process(pid)
                    proc_name = proc.name()

                    process_list.append({
                        'pid': pid,
                        'name': proc_name,
                    })
                except Exception as e:
                    print(f"处理进程 (PID: {pid}) 时发生错误: {e}")

            # 终止所有进程
            if process_list:
                kill_process(process_list)
                print("进程终止操作完成，等待系统释放资源...")
                time.sleep(RETRY_DELAY)  # 给予更长的时间让系统释放资源


# 修改find_file_process函数，使其接受文件地址列表作为参数
def find_file_process(failed_files: list):
    """
    查找占用指定文件列表中文件的进程，并返回包含根进程ID的进程信息字典
    参数: failed_files - 只包含源文件路径的列表
    返回: 字典，键为文件路径，值为占用该文件的进程信息列表
    """
    all_process_info = {}
    print(f"正在查找占用文件的进程，请等待...")

    try:
        # 初始化所有文件的进程信息列表
        for src in failed_files:
            all_process_info[src] = []

            # 检查文件是否存在
            if not os.path.exists(src):
                print(f"文件不存在: {src}")
                continue

        # 进程扫描阶段：遍历所有进程，一次性检查所有文件
        all_src_files = [src for src in failed_files if os.path.exists(src)]
        if all_src_files:
            all_process_info = _scan_processes_for_files(
                all_src_files, all_process_info)
        return all_process_info
    except Exception as e:
        print(f"查找占用文件的进程时发生错误: {e}")
        return all_process_info


def _scan_processes_for_files(file_paths, all_process_info):
    """\扫描所有进程，查找占用指定文件的进程"""
    try:
        # 遍历所有进程
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                # 检查进程打开的文件
                open_files = proc.info.get('open_files', [])
                if not open_files:
                    continue

                # 查找当前进程是否占用了我们关注的文件
                for file in open_files:
                    if file.path in file_paths:
                        # 找到占用文件的进程，获取根进程ID
                        process_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name']
                        }

                        # 添加到结果中
                        if process_info not in all_process_info[file.path]:
                            all_process_info[file.path].append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # 输出未找到进程的文件信息
        for file_path in file_paths:
            if file_path in all_process_info and not all_process_info[file_path]:
                print(f"未找到占用文件{file_path}的进程")
        return all_process_info

    except Exception as e:
        print(f"扫描进程时发生错误: {e}")
        return all_process_info

# 添加修改权限的函数到process_manager.py中


def get_root_process_id(pid):
    """
    获取进程的根进程ID
    """
    try:
        proc = psutil.Process(pid)
        while proc.parent() is not None:
            try:
                proc = proc.parent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 如果无法获取父进程信息，返回当前进程ID
                break
        return proc.pid
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return pid  # 如果无法获取进程信息，返回原进程ID


def kill_process(process_info):
    """
    终止指定的进程
    """
    if not process_info:
        return

    # 使用集合来存储已尝试终止的进程ID，避免重复操作
    terminated_pids = set()

    try:
        for info in process_info:
            pid = info['pid']
            # 尝试终止直接占用文件的进程（如果尚未终止过）
            if pid not in terminated_pids:
                try:
                    proc = psutil.Process(pid)
                    print(f"正在尝试终止进程: {info['name']} (PID: {pid})")
                    proc.terminate()
                    terminated_pids.add(pid)
                except psutil.NoSuchProcess:
                    print(f"进程 (PID: {pid}) 不存在")
                except psutil.AccessDenied:
                    print(f"没有权限终止进程 (PID: {pid})")
                except Exception as e:
                    print(f"终止进程 (PID: {pid}) 时发生错误: {e}")
    except Exception as e:
        print(f"终止进程时发生整体错误: {e}")
