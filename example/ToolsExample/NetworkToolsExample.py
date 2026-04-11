import psutil
import json
import time
import socket
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

def get_network_example_info(interval: float = 1.0) -> dict:
    """
    获取当前系统的网络详细信息示例。
    """
    results = {"状态": "success"}

    # 1. 获取网络流量统计 (累计)
    print("\n--- 网络流量统计 (累计) ---")
    net_io = psutil.net_io_counters()
    net_io_info = {
        "发送字节": _bytes_to_human(net_io.bytes_sent),
        "接收字节": _bytes_to_human(net_io.bytes_recv),
        "发送包数": net_io.packets_sent,
        "接收包数": net_io.packets_recv,
        "发送错误数": net_io.errin,
        "接收错误数": net_io.errout,
        "丢弃包数": net_io.dropin + net_io.dropout
    }
    print(f"发送字节: {net_io_info['发送字节']}, 接收字节: {net_io_info['接收字节']}")
    print(f"发送包数: {net_io_info['发送包数']}, 接收包数: {net_io_info['接收包数']}")
    results["累计流量统计"] = net_io_info

    # 2. 获取实时网速
    print(f"\n--- 实时网速 (每 {interval} 秒更新) ---")
    t0 = time.time()
    net_io_before = psutil.net_io_counters()
    time.sleep(interval)
    net_io_after = psutil.net_io_counters()
    t1 = time.time()

    send_speed = (net_io_after.bytes_sent - net_io_before.bytes_sent) / (t1 - t0)
    recv_speed = (net_io_after.bytes_recv - net_io_before.bytes_recv) / (t1 - t0)

    realtime_speed_info = {
        "发送速度": f"{_bytes_to_human(int(send_speed))}/s",
        "接收速度": f"{_bytes_to_human(int(recv_speed))}/s"
    }
    print(f"发送速度: {realtime_speed_info['发送速度']}, 接收速度: {realtime_speed_info['接收速度']}")
    results["实时网速"] = realtime_speed_info

    # 3. 获取网络接口地址 (IP 地址)
    print("\n--- 网络接口地址 ---")
    if_addrs_info = []
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET: # IPv4
                if_addrs_info.append({
                    "接口": interface,
                    "地址类型": "IPv4",
                    "地址": addr.address,
                    "子网掩码": addr.netmask,
                    "广播地址": addr.broadcast
                })
                print(f"接口: {interface}, IPv4 地址: {addr.address}, 子网掩码: {addr.netmask}")
            elif addr.family == socket.AF_INET6: # IPv6
                if_addrs_info.append({
                    "接口": interface,
                    "地址类型": "IPv6",
                    "地址": addr.address,
                    "子网掩码": addr.netmask
                })
                print(f"接口: {interface}, IPv6 地址: {addr.address}, 子网掩码: {addr.netmask}")
    results["网络接口地址"] = if_addrs_info

    # 4. 获取网络接口状态
    print("\n--- 网络接口状态 ---")
    if_stats_info = []
    for interface, stats in psutil.net_if_stats().items():
        if_stats_info.append({
            "接口": interface,
            "是否开启": stats.isup,
            "是否全双工": stats.duplex == psutil.NIC_DUPLEX_FULL,
            "速度": f"{stats.speed} Mbps" if stats.speed != 0 else "未知",
            "MTU": stats.mtu
        })
        print(f"接口: {interface}, 开启: {stats.isup}, 速度: {stats.speed} Mbps, MTU: {stats.mtu}")
    results["网络接口状态"] = if_stats_info

    # 5. 获取活跃网络连接
    print("\n--- 活跃网络连接 (部分显示) ---")
    connections_info = []
    count = 0
    for conn in psutil.net_connections(kind='inet'): # 只显示TCP/UDP连接
        if count >= 5: # 限制只显示5个
            break
        laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
        raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
        connections_info.append({
            "进程ID": conn.pid if conn.pid else "N/A",
            "本地地址": laddr,
            "远程地址": raddr,
            "状态": conn.status,
            "类型": str(conn.type)
        })
        print(f"PID: {conn.pid}, 本地: {laddr}, 远程: {raddr}, 状态: {conn.status}")
        count += 1
    results["活跃连接"] = connections_info

    return results

if __name__ == "__main__":
    network_info = get_network_example_info()
    print(json.dumps(network_info, indent=4, ensure_ascii=False))