import psutil
def get_cpu_usage(interval: float = 1.0) -> dict:
    """
    获取当前 CPU 的详细运行状态。

    Args:
        interval (float): 采样间隔时间（秒）。
                          默认为 1.0 秒。注意：此函数会阻塞当前线程 interval 秒
                          以计算准确的使用率。

    Returns:
        dict: 包含 CPU 信息的字典，格式如下：
        {
            "cpu_percent": float,           # 总 CPU 使用率 (%)
            "cpu_count_logical": int,       # 逻辑核心数 (线程数)
            "cpu_count_physical": int,      # 物理核心数
            "cpu_freq_current": str,        # 当前频率 (MHz)
            "cpu_ctx_switches": int,        # 上下文切换次数 (可选指标)
            "per_cpu_percent": list,        # 每个核心的独立使用率列表
            "load_avg": list                # 系统负载 [1分钟, 5分钟, 15分钟] (Unix/Linux有效)
        }
    """

    #1.获取CPU核心数量
    #（1）逻辑核心数：包含超线程技术后的核心数（任务管理器看到的框框数量）
    logical_count = psutil.cpu_count(logical=True)
    #（2）物理核心数：实际的硬件核心物理芯片数量
    physical_count = psutil.cpu_count(logical=False)

    #2.获取 CPU 频率信息
    # 注意：某些虚拟化环境或特定系统可能无法获取频率，需要做判空处理
    freq = psutil.cpu_freq()
    if freq:
        # 保留两位小数，单位通常是 MHz
        freq_current = f"{freq.current:.2f}MHz"
    else:
        freq_current = "Unknown"

    # 3. 获取 CPU 使用率
    # interval > 0 时，会阻塞等待指定时间来统计差值，数据才准确。
    # 如果 interval=0 或 None，则是非阻塞模式，但第一次调用通常返回 0.0。
    total_percent = psutil.cpu_percent(interval=interval)

    # 4. 获取每个核心的独立使用率
    # 这对于大模型判断是否是“单核性能瓶颈”（即某个核跑满，其他核空闲）非常有用
    per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)

    # 5. 获取系统负载 (Load Average)
    # 这是一个非常重要的指标，表示“有多少进程在排队等待CPU”。
    # Windows 上 psutil 通常通过模拟或返回 None，Linux/Mac 上返回 (1min, 5min, 15min) 的负载元组。
    try:
        if hasattr(psutil, "getloadavg"):
            load_avg = psutil.getloadavg()
        else:
            load_avg = "Not Available on Windows"
    except OSError:
        load_avg = "Permission Denied"

    # 6.获取 CPU 统计信息，如上下文切换
    # 上下文切换过高通常意味着进程争抢资源严重
    ctx_switches = psutil.cpu_stats().ctx_switches

    # 组装返回结果
    # 这种字典结构非常适合直接转为 JSON 投喂给大模型
    return {
        "状态": "success",
        "总CPU使用率": total_percent,          # 总体使用率，最直观的指标
        "逻辑核心数": logical_count,   
        "物理核心数": physical_count,  
        "当前CPU频率": freq_current,     
        "每个核心使用率": per_cpu_percent,      # 列表：[10.2, 5.5, 80.1, ...]
        "系统负载": load_avg,                
        "上下文切换次数": ctx_switches         
    }
    