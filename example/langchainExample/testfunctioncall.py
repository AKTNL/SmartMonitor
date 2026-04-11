import psutil
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

# 普通函数：真正执行逻辑
def _get_cpu_performance() -> float:
    """获取当前系统的CPU利用率（百分比）"""
    return psutil.cpu_percent(interval=1)

# 工具函数：用于绑定给 LLM
@tool
def get_cpu_performance() -> float:
    """获取当前系统的CPU利用率（百分比）"""
    return _get_cpu_performance()

def _get_memory_usage() -> float:
    """获取当前内存使用率（百分比）"""
    return psutil.virtual_memory().percent

@tool
def get_memory_usage() -> float:
    """获取当前内存使用率（百分比）"""
    return _get_memory_usage()

def _get_disk_usage(path: str = "/") -> float:
    """获取指定路径的磁盘使用率（百分比），默认根目录，异常时返回-1"""
    try:
        usage = psutil.disk_usage(path)
        return round(usage.used / usage.total * 100, 2)
    except Exception as e:
        print(f"⚠️ 磁盘查询失败: {e}")  # 只打印错误，不返回
        return -1.0  # 用无效值表示错误（-1.0 是 float 类型）
    
@tool
def get_disk_usage(path: str = "/") -> float:
    """获取指定路径的磁盘使用率（百分比），默认根目录"""
    return _get_disk_usage(path)

# 初始化模型
llm = ChatOllama(model="qwen2.5:7b-instruct").bind_tools([get_cpu_performance,get_memory_usage,get_disk_usage])

# 调用
response = llm.invoke("我当前的CPU利用率是多少？")

if hasattr(response, 'tool_calls') and response.tool_calls:
    # 执行真正的逻辑函数
    cpu_usage = _get_cpu_performance()
    print(f"CPU 利用率: {cpu_usage}%")
else:
    print("模型回复:", response.content)

response2 = llm.invoke("我当前的内存使用率是多少？")

if hasattr(response2, 'tool_calls') and response2.tool_calls:
    # 执行真正的逻辑函数
    memory_usage = _get_memory_usage()  # 假设返回百分比值
    if memory_usage < 40:
        print(f"内存使用率：{memory_usage}% ✅ 资源充足，可正常运行或增加任务。")
    elif 40 <= memory_usage <= 85:
        print(f"内存使用率：{memory_usage}% ⚠️ 资源占用中等，建议监控趋势。")
    else:
        print(f"内存使用率：{memory_usage}% ⛔ 资源紧张！请优化任务或释放内存。")

else:
    print("模型回复:", response2.content)

response3 = llm.invoke("我当前的磁盘使用率是多少？")

if hasattr(response3, 'tool_calls') and response3.tool_calls:
    disk_usage = _get_disk_usage()
    if disk_usage == -1.0:
        print("❌ 磁盘使用率查询失败，请检查路径或权限")
    else:
        print(f"磁盘 使用率: {disk_usage:.2f}%")  # 保留两位小数
else:
    print("模型回复:", response3.content)