import psutil
from langchain_core.tools import tool
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage
)
from langchain_ollama import ChatOllama


# ======================
# 1. 定义工具
# ======================
@tool
def get_cpu_performance() -> float:
    """获取当前 CPU 利用率（百分比）"""
    return psutil.cpu_percent(interval=1)


@tool
def get_memory_usage() -> float:
    """获取当前内存使用率（百分比）"""
    return psutil.virtual_memory().percent


@tool
def get_disk_usage(path: str = "/") -> float:
    """获取指定路径的磁盘使用率（百分比），默认根目录"""
    try:
        usage = psutil.disk_usage(path)
        return round(usage.used / usage.total * 100, 2)
    except Exception as e:
        return f"错误: {e}"


# 工具注册
tools = [get_cpu_performance, get_memory_usage, get_disk_usage]
tool_map = {t.name: t for t in tools}


# ======================
# 2. 带工具绑定的 LLM
# ======================
llm = ChatOllama(model="qwen2.5:7b-instruct", temperature=0).bind_tools(tools)


# ======================
# 3. 核心函数：支持多工具调用
# ======================
def ask_sysagent(question: str) -> str:
    """
    向系统助手提问，自动调用所需工具（可多个），返回综合分析
    """
    # 第一步：构造带系统提示的消息
    messages = [
        SystemMessage(content=(
            "你是一个专业的 openEuler 系统性能分析师。\n"
            "你可以调用以下工具获取真实指标：\n"
            "- get_cpu_performance(): CPU 使用率\n"
            "- get_memory_usage(): 内存使用率\n"
            "- get_disk_usage(path='/'): 磁盘使用率\n"
            "请根据用户问题决定调用哪些工具。必须基于真实返回值进行分析，不要猜测。\n"
            "分析标准：\n"
            "  • CPU < 30% 空闲，30~70% 正常，>90% 过载\n"
            "  • 内存 > 85% 需警惕\n"
            "  • 磁盘 > 90% 有风险\n"
            "用简洁中文给出综合判断和建议。"
        )),
        HumanMessage(content=question)
    ]

    # 第二步：让 LLM 决定调用哪些工具
    ai_response: AIMessage = llm.invoke(messages)

    # 如果没有工具调用，直接返回
    if not ai_response.tool_calls:
        return ai_response.content

    # 第三步：执行所有工具调用
    tool_messages = []
    for tool_call in ai_response.tool_calls:
        name = tool_call["name"]
        args = tool_call.get("args", {})
        tool_id = tool_call["id"]

        if name in tool_map:
            try:
                result = tool_map[name].invoke(args)
            except Exception as e:
                result = f"执行出错: {e}"
        else:
            result = f"未知工具: {name}"

        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_id)
        )

    # 第四步：将所有工具结果回填，生成最终回答
    final_messages = messages + [ai_response] + tool_messages
    final_response: AIMessage = llm.invoke(final_messages)

    return final_response.content


# ======================
# 4. 测试
# ======================
if __name__ == "__main__":
    # 测试多工具场景
    question = "我当前的内存利用率和CPU利用率是多少？请分析是否正常。"
    print("👤 问题:", question)
    print("\n🧠 助手回答:")
    print(ask_sysagent(question))