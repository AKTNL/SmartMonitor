import os
import time
import platform
from pathlib import Path
import json

def _bytes_to_human(n):
    """
    将字节数转换为人类可读的格式 (例如, 1024 -> 1KB)。
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return f'{value:.2f} {s}B'
    return f'{n:.2f} B'

def get_file_example_info(top_n_large_files: int = 5) -> dict:
    """
    获取文件系统总体情况的示例，包括目录内容概览和查找大文件。
    """
    results = {"状态": "success"}

    # 1. 列出目录内容概览
    print("\n--- 目录内容概览 ---")
    target_dir = "/" # 硬编码为Linux根目录
    directory_list_result = {}
    try:
        items = []
        files_count = 0
        dirs_count = 0
        total_size = 0
        for entry in os.scandir(target_dir):
            try:
                if entry.is_file():
                    files_count += 1
                    total_size += entry.stat().st_size
                elif entry.is_dir():
                    dirs_count += 1
            except Exception:
                pass # Ignore permission errors or broken symlinks

        # Display a few entries for overview
        display_items = []
        with os.scandir(target_dir) as it:
            count = 0
            for entry in it:
                if count >= 10: # 限制只显示前10个条目作为概览
                    break
                name = entry.name + ("/" if entry.is_dir() else "")
                size = "DIR"
                if entry.is_file():
                    try:
                        size = _bytes_to_human(entry.stat().st_size)
                    except:
                        size = "?"
                display_items.append(f"{name:<30} | {size}")
                count += 1

        directory_list_result = {
            "目录": target_dir,
            "文件总数": files_count,
            "子目录总数": dirs_count,
            "总大小": _bytes_to_human(total_size),
            "概览条目": display_items
        }
        print(f"目录: {directory_list_result['目录']}")
        print(f"  文件总数: {files_count}, 子目录总数: {dirs_count}, 总大小: {_bytes_to_human(total_size)}")
        print("  部分条目:")
        for item in display_items:
            print(f"    {item}")
    except Exception as e:
        directory_list_result = {"错误": f"列出目录概览失败: {e}"}
        print(f"列出目录概览失败: {e}")
    results["目录概览"] = directory_list_result

    # 2. 查找指定目录中的大文件
    print(f"\n--- 查找目录中最大的 {top_n_large_files} 个文件 ---")
    large_files_result = []
    try:
        file_sizes = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    file_sizes.append((size, file_path))
                except Exception:
                    pass # Ignore permission errors or inaccessible files

        file_sizes.sort(key=lambda x: x[0], reverse=True)

        for size, path in file_sizes[:top_n_large_files]:
            large_files_result.append({
                "路径": path,
                "大小": _bytes_to_human(size),
                "大小_字节": size
            })
            print(f"  大小: {_bytes_to_human(size)}, 路径: {path}")
    except Exception as e:
        large_files_result = {"错误": f"查找大文件失败: {e}"}
        print(f"查找大文件失败: {e}")
    results["大文件列表"] = large_files_result

    return results

if __name__ == "__main__":
    file_example_info = get_file_example_info()
    print(json.dumps(file_example_info, indent=4, ensure_ascii=False))