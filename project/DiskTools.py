import psutil

def _bytes_to_gb_str(bytes_value: int) -> str:
    """内部辅助函数：将字节转换为 GB 字符串，保留2位小数"""
    gb_value = bytes_value / (1024 ** 3)
    return f"{gb_value:.2f} GB"

def get_disk_usage() -> dict:
    """
    获取系统磁盘状态。
    
    特点：
    1. 自动过滤 tmpfs, overlay, squashfs 等非物理存储分区。
    2. 重点监控 /, /home, /boot, /var 等关键路径。
    
    Returns:
        dict: 包含分区列表和 IO 统计
    """
    # --- 1. 定义需要忽略的文件系统类型 ---
    # 在 openEuler/Linux 服务器上，这些通常是内存盘或容器层，不需要监控
    ignore_types = {
        'tmpfs', 'devtmpfs', 'overlay', 'squashfs', 'iso9660', 'tracefs'
    }
    
    partitions_list = []
    
    # 1. 获取所有挂载的分区
    for partition in psutil.disk_partitions(all=False):
        # 过滤逻辑：
        # 1. 如果文件系统类型在忽略列表中，跳过
        # 2. 如果设备路径包含 'loop' (通常是 snap 应用或虚拟设备)，跳过
        if partition.fstype in ignore_types or '/loop' in partition.device:
            continue
            
        try:
            # 获取具体挂载点的使用情况
            usage = psutil.disk_usage(partition.mountpoint)
            
            partitions_list.append({
                "设备": partition.device,         # 设备路径 (如 /dev/sda1)
                "挂载点": partition.mountpoint, # 挂载点 (如 /, /home)
                "文件系统类型": partition.fstype,         # 文件系统 (如 xfs, ext4)
                "总容量": _bytes_to_gb_str(usage.total),
                "已用容量": _bytes_to_gb_str(usage.used),
                "空闲容量": _bytes_to_gb_str(usage.free),
                "使用率":  f"{usage.percent}%"
            })
        except PermissionError:
            # 某些特殊挂载点可能无权访问
            continue

    # --- 2. 获取磁盘 IO 统计 ---
    # 监控硬盘读写负载
    try:
        io = psutil.disk_io_counters()
        io_info = {
            "读取次数": io.read_count,
            "写入次数": io.write_count,
            "读取字节": _bytes_to_gb_str(io.read_bytes),
            "写入字节": _bytes_to_gb_str(io.write_bytes)
        }
    except Exception:
        # 某些虚拟化环境可能获取不到 IO 计数
        io_stats = {
            "读取次数": 0, "写入次数": 0, 
            "读取字节": "0.00 GB", "写入字节": "0.00 GB"
        }

    return {
        "状态": "success",
        "分区信息": partitions_list,
        "IO统计": io_info
    }
