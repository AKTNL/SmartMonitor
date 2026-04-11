import psutil
import json
import time
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

def get_process_example_info(interval: float = 1.0) -> dict:
    """
    获取当前系统进程总体情况的示例，包括高资源占用进程、进程概览和进程总数。
    """
    results = {"状态": "success"}

    # === 1. 获取资源占用最高的进程 (Top 5 by CPU + Memory) ===
    print("\n--- 资源占用最高的进程 (Top 5) ---")
    processes = []
    # 第一步：创建所有有效进程对象并初始化 cpu_percent
    for proc_info in psutil.process_iter(['pid', 'name', 'username']):
        try:
            p = psutil.Process(proc_info.pid)
            p.cpu_percent(interval=0)  # 初始化（记录起始 CPU 时间）
            processes.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # 等待 interval 秒以获取有意义的 CPU 使用率
    time.sleep(interval)

    # 第二步：收集实际 CPU 和内存数据
    process_stats = []
    for p in processes:
        try:
            cpu = p.cpu_percent(interval=0)  # 获取实际 CPU 使用率
            mem_info = p.memory_info()
            process_stats.append({
                "PID": p.pid,
                "名称": p.name(),
                "用户": p.username(),
                "CPU使用率": f"{cpu:.2f}%",
                "内存使用": _bytes_to_human(mem_info.rss)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print(f"获取进程 {p.pid} 信息时出错: {e}")
            continue

    # 按 CPU 使用率排序，取 Top 5
    top_processes = sorted(process_stats, key=lambda x: float(x["CPU使用率"].rstrip('%')), reverse=True)[:5]
    for item in top_processes:
        print(f"PID: {item['PID']}, 名称: {item['名称']}, CPU: {item['CPU使用率']}, 内存: {item['内存使用']}")
    results["高资源占用进程"] = top_processes

    # === 2. 进程概览 (前20个) ===
    print("\n--- 进程概览 (前20个) ---")
    process_overview = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info']):
        try:
            mem_info = proc.info['memory_info']
            process_overview.append({
                "PID": proc.info['pid'],
                "名称": proc.info['name'],
                "状态": proc.info['status'],
                "内存使用": _bytes_to_human(mem_info.rss) if mem_info else "N/A"
            })
            if len(process_overview) >= 20: # 限制只显示前20个进程作为概览
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print(f"获取进程概览信息时出错: {e}")
            continue
    results["进程概览"] = process_overview
    for item in process_overview:
        print(f"PID: {item['PID']}, 名称: {item['名称']}, 状态: {item['状态']}, 内存: {item['内存使用']}")

    # === 3. 进程总数 ===
    print("\n--- 进程数量 ---")
    process_count = len(psutil.pids())
    print(f"当前运行进程总数: {process_count}")
    results["进程总数"] = process_count

    return results

if __name__ == "__main__":
    process_info = get_process_example_info(interval=1.0)
    print("\n=== 最终结果 (JSON) ===")
    print(json.dumps(process_info, indent=4, ensure_ascii=False))