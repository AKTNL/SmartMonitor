import psutil
import json
import os

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

def get_disk_example_info() -> dict:
    """
    获取当前系统的磁盘详细信息示例。
    """
    # 1. 获取磁盘分区信息
    partitions_info = []
    ignore_types = {'tmpfs', 'devtmpfs', 'overlay', 'squashfs', 'iso9660', 'tracefs'}

    print("\n--- 磁盘分区信息 ---")
    for partition in psutil.disk_partitions(all=False):
        if partition.fstype in ignore_types or '/loop' in partition.device:
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            partitions_info.append({
                "设备": partition.device,
                "挂载点": partition.mountpoint,
                "文件系统类型": partition.fstype,
                "总容量": _bytes_to_human(usage.total),
                "已用容量": _bytes_to_human(usage.used),
                "空闲容量": _bytes_to_human(usage.free),
                "使用率": f"{usage.percent}%"
            })
            print(f"设备: {partition.device}, 挂载点: {partition.mountpoint}, 文件系统: {partition.fstype}")
            print(f"  总容量: {_bytes_to_human(usage.total)}, 已用: {_bytes_to_human(usage.used)}, 空闲: {_bytes_to_human(usage.free)}, 使用率: {usage.percent}%")
        except PermissionError:
            print(f"无权访问挂载点: {partition.mountpoint}")
            continue
        except Exception as e:
            print(f"获取分区 {partition.mountpoint} 信息失败: {e}")

    # 2. 获取磁盘 I/O 统计
    io_info = {}
    try:
        io = psutil.disk_io_counters()
        io_info = {
            "读取次数": io.read_count,
            "写入次数": io.write_count,
            "读取字节": _bytes_to_human(io.read_bytes),
            "写入字节": _bytes_to_human(io.write_bytes)
        }
        print("\n--- 磁盘 I/O 统计 ---")
        print(f"读取次数: {io.read_count}, 写入次数: {io.write_count}")
        print(f"读取字节: {_bytes_to_human(io.read_bytes)}, 写入字节: {_bytes_to_human(io.write_bytes)}")
    except Exception:
        io_info = "不可用"
        print("\n--- 磁盘 I/O 统计 ---")
        print("磁盘 I/O 统计不可用")

    return {
        "状态": "success",
        "分区信息": partitions_info,
        "IO统计": io_info
    }

if __name__ == "__main__":
    disk_info = get_disk_example_info()
    print(json.dumps(disk_info, indent=4, ensure_ascii=False))