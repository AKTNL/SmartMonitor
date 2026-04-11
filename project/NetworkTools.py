import psutil
import time
import socket
import json

def _bytes_to_human(n: int) -> str:
    """内部工具：字节转人类可读格式"""
    symbols = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i * 10)
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f %s' % (value, s)
    return "%s B" % n


def get_network_general_info(interval: float = 1.0) -> dict:
    """
    获取符合 AgentState 要求的全量网络信息。
    包括：累计流量、实时网速、接口地址、接口状态、活跃连接。

    Args:
        interval (float): 测速采样间隔，默认 1.0 秒。
    """
    try:
        # 1. 累计流量统计 (启动时的数据)
        net_io_start = psutil.net_io_counters()

        # 2. 实时网速 (采样)
        time.sleep(interval)
        net_io_end = psutil.net_io_counters()

        sent_speed = (net_io_end.bytes_sent - net_io_start.bytes_sent) / interval
        recv_speed = (net_io_end.bytes_recv - net_io_start.bytes_recv) / interval

        # 3. 网络接口地址
        if_addrs_data = []
        if_addrs = psutil.net_if_addrs()
        for iface, addrs in if_addrs.items():
            for addr in addrs:
                addr_info = {
                    "接口": iface,
                    "地址类型": "IPv4" if addr.family == socket.AF_INET else (
                        "IPv6" if addr.family == socket.AF_INET6 else str(addr.family)),
                    "地址": addr.address,
                    "子网掩码": addr.netmask,
                    "广播地址": addr.broadcast if addr.broadcast else "N/A"
                }
                if_addrs_data.append(addr_info)

        # 4. 网络接口状态
        if_stats_data = []
        if_stats = psutil.net_if_stats()
        for iface, stat in if_stats.items():
            if_stats_data.append({
                "接口": iface,
                "是否开启": stat.isup,
                "是否全双工": stat.duplex == psutil.NIC_DUPLEX_FULL,
                "速度": f"{stat.speed} Mbps",
                "MTU": stat.mtu
            })

        # 5. 活跃连接 (Top 5 TCP/UDP)
        connections_data = []
        try:
            # 需要 root 权限才能看到所有进程的连接，普通用户只能看到自己的
            conns = psutil.net_connections(kind='inet')
            # 简单过滤：只看 ESTABLISHED 或 LISTEN
            active_conns = [c for c in conns if c.status in ['ESTABLISHED', 'LISTEN']]

            for c in active_conns[:5]:  # 限制显示前 5 个
                laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
                raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
                connections_data.append({
                    "进程ID": c.pid,
                    "本地地址": laddr,
                    "远程地址": raddr,
                    "状态": c.status,
                    "类型": "TCP" if c.type == socket.SOCK_STREAM else (
                        "UDP" if c.type == socket.SOCK_DGRAM else str(c.type))
                })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections_data.append({"错误": "无法获取完整连接列表(权限不足)"})

        # 组装最终 JSON
        return {
            "状态": "success",
            "累计流量统计": {
                "发送字节": _bytes_to_human(net_io_end.bytes_sent),
                "接收字节": _bytes_to_human(net_io_end.bytes_recv),
                "发送包数": net_io_end.packets_sent,
                "接收包数": net_io_end.packets_recv,
                "发送错误数": net_io_end.errin + net_io_end.errout,  # 简化合并
                "接收错误数": net_io_end.errin,
                "丢弃包数": net_io_end.dropin + net_io_end.dropout
            },
            "实时网速": {
                "发送速度": f"{_bytes_to_human(sent_speed)}/s",
                "接收速度": f"{_bytes_to_human(recv_speed)}/s"
            },
            "网络接口地址": if_addrs_data,
            "网络接口状态": if_stats_data,
            "活跃连接": connections_data
        }

    except Exception as e:
        return {"状态": "error", "信息": str(e)}


if __name__ == "__main__":


    print("正在测速(1秒)...")
    print(json.dumps(get_network_general_info(), indent=4, ensure_ascii=False))