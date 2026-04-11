import psutil
import time
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


def get_process_general_info() -> dict:
    """
    获取符合 AgentState 要求的进程概览信息。
    包括：高资源占用进程(Top 5)、进程列表概览(前20)、进程总数。
    """
    try:
        # 获取所有进程的迭代器，一次性获取所需信息以提高效率
        # 注意：cpu_percent 在 interval=None 时第一次调用可能不准确，这里为了速度取瞬时值
        # 若需要更精确，可先调用 process_iter 预热，或接受短暂阻塞
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info', 'status']):
            try:
                # 触发一次 cpu 计算 (部分系统需要)
                p.cpu_percent()
                processes.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        total_count = len(processes)

        # 1. 准备数据列表
        proc_list = []
        for p in processes:
            try:
                info = p.info
                # 内存使用取 RSS (常驻内存)
                mem_size = info['memory_info'].rss if info['memory_info'] else 0

                proc_data = {
                    "PID": info['pid'],
                    "名称": info['name'],
                    "用户": info['username'],
                    "CPU使用率": f"{info['cpu_percent']}%",
                    "CPU数值": info['cpu_percent'],  # 用于排序
                    "内存使用": _bytes_to_human(mem_size),
                    "内存数值": mem_size,  # 用于排序
                    "状态": info['status']
                }
                proc_list.append(proc_data)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 2. 计算高资源占用进程 (Top 5) - 综合 CPU 和 内存 排序
        # 这里简单策略：优先按 CPU 降序，若 CPU 相同按内存降序
        sorted_by_resource = sorted(proc_list, key=lambda x: (x["CPU数值"], x["内存数值"]), reverse=True)
        top_5 = sorted_by_resource[:5]

        # 清理用于排序的临时字段
        final_top_5 = []
        for p in top_5:
            # 构造符合文档要求的字段
            final_top_5.append({
                "PID": p["PID"],
                "名称": p["名称"],
                "用户": p["用户"],
                "CPU使用率": p["CPU使用率"],
                "内存使用": p["内存使用"]
            })

        # 3. 进程概览 (前 20 个，通常按 PID 或默认顺序)
        # 文档示例中包含 PID, 名称, 状态, 内存使用
        overview_20 = []
        for p in proc_list[:20]:
            overview_20.append({
                "PID": p["PID"],
                "名称": p["名称"],
                "状态": p["状态"],
                "内存使用": p["内存使用"]
            })

        return {
            "状态": "success",
            "高资源占用进程": final_top_5,
            "进程概览": overview_20,
            "进程总数": total_count
        }

    except Exception as e:
        return {"状态": "error", "信息": str(e)}


if __name__ == "__main__":


    # 稍微预热一下以便 CPU 数据更准确
    time.sleep(0.1)
    print(json.dumps(get_process_general_info(), indent=4, ensure_ascii=False))