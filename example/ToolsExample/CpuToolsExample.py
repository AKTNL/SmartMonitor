
import psutil
import json

def get_cpu_example_info(interval: float = 1.0) -> dict:
    """
    获取当前 CPU 的详细运行状态示例。
    """
    # 1. 获取CPU核心数量
    logical_count = psutil.cpu_count(logical=True)
    print(f"逻辑核心数 (线程数): {logical_count}")
    physical_count = psutil.cpu_count(logical=False)
    print(f"物理核心数: {physical_count}")

    # 2. 获取 CPU 频率信息
    freq = psutil.cpu_freq()
    if freq:
        freq_current = f"{freq.current:.2f}MHz"
        print(f"当前频率: {freq_current}")
    else:
        freq_current = "Unknown"
        print(f"当前频率: {freq_current}")

    # 3. 获取 CPU 使用率
    total_percent = psutil.cpu_percent(interval=interval)
    print(f"总 CPU 使用率 (%): {total_percent}")

    # 4. 获取每个核心的独立使用率
    per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)
    print(f"每个核心的独立使用率列表: {per_cpu_percent}")

    # 5. 获取系统负载 (Load Average)
    try:
        if hasattr(psutil, "getloadavg"):
            load_avg = psutil.getloadavg()
            print(f"系统负载 [1分钟, 5分钟, 15分钟]: {load_avg}")
        else:
            load_avg = "Not Available on Windows"
            print(f"系统负载: {load_avg}")
    except OSError:
        load_avg = "Permission Denied"
        print(f"系统负载: {load_avg}")

    # 6. 获取 CPU 统计信息，如上下文切换
    ctx_switches = psutil.cpu_stats().ctx_switches
    print(f"上下文切换次数: {ctx_switches}")

    return {
        "状态": "success",
        "总CPU使用率": total_percent,
        "逻辑核心数": logical_count,
        "物理核心数": physical_count,
        "当前CPU频率": freq_current,
        "每个核心使用率": per_cpu_percent,
        "系统负载": load_avg,
        "上下文切换次数": ctx_switches
    }

if __name__ == "__main__":
    cpu_info = get_cpu_example_info()
    print(json.dumps(cpu_info, indent=4, ensure_ascii=False))