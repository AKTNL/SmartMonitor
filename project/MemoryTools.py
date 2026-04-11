import psutil
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


def get_memory_general_info() -> dict:
    """
    获取符合 AgentState 要求的全量内存信息。
    包括：物理内存、交换分区、Linux特有字段及警报状态。
    """
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # 警报检查 (阈值 80%)
        alert_status = "正常"
        if mem.percent > 80:
            alert_status = "⚠️ 内存使用率过高"

        # 基础数据
        info = {
            "状态": "success",
            "总内存": _bytes_to_human(mem.total),
            "可用内存": _bytes_to_human(mem.available),
            "内存使用率": f"{mem.percent}%",
            "已用内存": _bytes_to_human(mem.used),
            "空闲内存": _bytes_to_human(mem.free),

            # 交换分区
            "交换分区总量": _bytes_to_human(swap.total),
            "交换分区已用": _bytes_to_human(swap.used),
            "交换分区空闲": _bytes_to_human(swap.free),
            "交换分区使用率": f"{swap.percent}%",
            "内存警报": alert_status
        }

        # Linux 特有字段 (兼容性处理)
        # Windows/MacOS 上这些字段可能不存在，设为 N/A 或 0
        info["活跃内存"] = _bytes_to_human(getattr(mem, 'active', 0)) if hasattr(mem, 'active') else "N/A"
        info["不活跃内存"] = _bytes_to_human(getattr(mem, 'inactive', 0)) if hasattr(mem, 'inactive') else "N/A"
        info["缓冲区"] = _bytes_to_human(getattr(mem, 'buffers', 0)) if hasattr(mem, 'buffers') else "N/A"
        info["缓存"] = _bytes_to_human(getattr(mem, 'cached', 0)) if hasattr(mem, 'cached') else "N/A"
        info["共享内存"] = _bytes_to_human(getattr(mem, 'shared', 0)) if hasattr(mem, 'shared') else "0.00 B"

        return info

    except Exception as e:
        return {"状态": "error", "信息": str(e)}


if __name__ == "__main__":


    print(json.dumps(get_memory_general_info(), indent=4, ensure_ascii=False))