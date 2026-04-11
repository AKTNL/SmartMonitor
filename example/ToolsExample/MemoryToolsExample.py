import psutil
import json
import os
import sys

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

def get_memory_example_info() -> dict:
    """
    获取当前系统的内存详细信息示例。
    """
    # 1. 获取物理内存的整体统计信息
    virtual_memory = psutil.virtual_memory()
    print(f"psutil.virtual_memory(): {virtual_memory}")
    print(f"总内存: {_bytes_to_human(virtual_memory.total)}")
    print(f"可用内存: {_bytes_to_human(virtual_memory.available)}")
    print(f"内存使用率: {virtual_memory.percent}%")
    print(f"已用内存: {_bytes_to_human(virtual_memory.used)}")
    print(f"空闲内存: {_bytes_to_human(virtual_memory.free)}")
    
    active_memory = "N/A"
    inactive_memory = "N/A"
    buffers_memory = "N/A"
    cached_memory = "N/A"
    if sys.platform.startswith('linux'):
        active_memory = _bytes_to_human(virtual_memory.active)
        inactive_memory = _bytes_to_human(virtual_memory.inactive)
        buffers_memory = _bytes_to_human(virtual_memory.buffers)
        cached_memory = _bytes_to_human(virtual_memory.cached)
    print(f"活跃内存: {active_memory}")
    print(f"不活跃内存: {inactive_memory}")
    print(f"缓冲区: {buffers_memory}")
    print(f"缓存: {cached_memory}")

    # 2. 获取交换分区的整体统计信息
    swap_memory = psutil.swap_memory()
    print(f"\npsutil.swap_memory(): {swap_memory}")
    print(f"交换分区总量: {_bytes_to_human(swap_memory.total)}")
    print(f"交换分区已用: {_bytes_to_human(swap_memory.used)}")
    print(f"交换分区空闲: {_bytes_to_human(swap_memory.free)}")
    print(f"交换分区使用率: {swap_memory.percent}%")

    # 3. 获取共享内存信息 (主要在 Linux 上)
    shared_memory = getattr(virtual_memory, 'shared', 0) # 'shared' 属性可能不存在于所有系统
    print(f"\npsutil.virtual_memory().shared: {_bytes_to_human(shared_memory)}")

    # 4. 获取特定进程的内存使用详情 (以当前进程为例)
    current_process = psutil.Process(os.getpid())
    process_memory_info = current_process.memory_info()
    print(f"\npsutil.Process.memory_info() (当前进程): {process_memory_info}")
    print(f"RSS (Resident Set Size): {_bytes_to_human(process_memory_info.rss)}")
    print(f"VMS (Virtual Memory Size): {_bytes_to_human(process_memory_info.vms)}")

    return {
        "状态": "success",
        "总内存": _bytes_to_human(virtual_memory.total),
        "可用内存": _bytes_to_human(virtual_memory.available),
        "内存使用率": f"{virtual_memory.percent}%",
        "已用内存": _bytes_to_human(virtual_memory.used),
        "空闲内存": _bytes_to_human(virtual_memory.free),
        "活跃内存": active_memory,
        "不活跃内存": inactive_memory,
        "缓冲区": buffers_memory,
        "缓存": cached_memory,
        "共享内存": _bytes_to_human(shared_memory),
        "交换分区总量": _bytes_to_human(swap_memory.total),
        "交换分区已用": _bytes_to_human(swap_memory.used),
        "交换分区空闲": _bytes_to_human(swap_memory.free),
        "交换分区使用率": f"{swap_memory.percent}%",
        "内存警报": "正常" # 示例中不包含警报逻辑，此处为占位
    }

if __name__ == "__main__":
    memory_info = get_memory_example_info()
    print(json.dumps(memory_info, indent=4, ensure_ascii=False))