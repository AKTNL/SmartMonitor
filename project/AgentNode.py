import os
import platform
from langchain_ollama import ChatOllama
from .AgentState import AgentState

from .MemoryTools import get_memory_general_info
from .NetworkTools import get_network_general_info
from .ProcessTools import get_process_general_info

from .CpuTools import get_cpu_usage
from .DiskTools import get_disk_usage
from .FileTools import get_file_usage
from .RouterTools import string_match_router, RetrieveRouter, LLMArbitrator


class AgentNode:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.llm = ChatOllama(model=model_name)

    def start_node(self, state: AgentState):
        """
        开始节点
        """
        # print("\n" + "=" * 20 + " [Node: Start] " + "=" * 20)

        # print(f"Current State: {state}")

    def system_monitor_node(self, state: AgentState):
        """
        [综合监控节点]
        集成所有工具，获取系统完整快照。
        """
        # print("\n" + "=" * 20 + " [Node: System Monitor] " + "=" * 20)
        last_message = state["messages"][-1]["content"]
        string_match_result = string_match_router(last_message)
        # 1. 采集数据
        print("正在采集系统数据")

        system_info = {}
        if "cpu" in string_match_result:
            print("  - 正在采集 CPU 信息...")
            system_info["cpu"] = get_cpu_usage()

        if "disk" in string_match_result:
            print("  - 正在采集 磁盘 信息...")
            system_info["disk"] = get_disk_usage()

        if "memory" in string_match_result:
            print("  - 正在采集 内存 信息...")
            system_info["memory"] = get_memory_general_info()

        if "network" in string_match_result:
            print("  - 正在采集 网络 信息...")
            system_info["network"] = get_network_general_info()

        if "process" in string_match_result:
            print("  - 正在采集 进程 信息...")
            system_info["processes"] = get_process_general_info()

        if "file" in string_match_result:
            print("  - 正在采集 文件 信息...")
            if platform.system() == "Windows":
                base_dir = os.getcwd()
            else:
                base_dir = "/var/log"
            system_info["file"] = get_file_usage(last_message, base_dir)

        print("数据采集完成")
        # print(f"Current State (before update): {json.dumps(state, indent=4, ensure_ascii=False)}")
        return {"system_info": system_info}



    def analysis_node(self, state: AgentState):
        """
        [分析节点]
        通用的 LLM 分析器，将 system_info 转换为自然语言报告。
        """
        # print("\n" + "=" * 20 + " [Node: Analysis] " + "=" * 20)

        system_info = state.get("system_info", {})
        last_message = state["messages"][-1]["content"]

        # # 使用统一的格式化函数
        # report_text = self._data_to_text(system_info)

        print("📄 生成上下文报告...")
        # print(report_text) # 调试用

        analysis_prompt = f"""
        你是一个专业的系统管理员。请根据下面的【系统状态报告】回答用户的问题。

        【系统状态报告】
        {system_info}

        【用户问题】
        {last_message}

        【回复要求】
        1. 必须基于报告中的真实数据，不要编造。
        2. 语言简洁专业。
        3. 如果是进程操作（如杀进程），明确告知结果。
        """

        messages = [
            {"role": "system", "content": "你是一个有用的系统助手。"},
            {"role": "human", "content": analysis_prompt}
        ]

        print("🤖 调用模型生成回复...")
        response = self.llm.invoke(messages)
        #print(f"Current State: {json.dumps(state, indent=4, ensure_ascii=False)}")
        return {"messages": state["messages"] + [{"role": "ai", "content": response.content}]}

    def simple_chat_node(self, state: AgentState):
        """闲聊节点"""
        # print("\n" + "=" * 20 + " [Node: Simple Chat] " + "=" * 20)
        response = self.llm.invoke(state["messages"])
        return {"messages": state["messages"] + [{"role": "ai", "content": response.content}]}

    def process_node(self, state: AgentState):
        """进程节点：获取进程 Top5 和概览"""
        # print("\n" + "=" * 20 + " [Node: Process Tool] " + "=" * 20)
        # 直接调用工具
        data = get_process_general_info()
        return {"system_info": {"processes": data}}

    def file_node(self, state: AgentState):
        """文件分析节点：智能判断 读取内容 / 查看属性 / 扫描大文件 / 列出目录"""
        # print("\n" + "=" * 20 + " [Node: File Tool] " + "=" * 20)

        last_msg = state["messages"][-1]["content"]

        # 确定基准目录
        if platform.system() == "Windows":
            base_dir = os.getcwd()
        else:
            base_dir = "/var/log"

        file_info = get_file_usage(last_msg, base_dir)
        return {"system_info": {"file": file_info}}

    def cpu_node(self, state: AgentState):
        """CPU 监控节点：获取数据并生成报告"""
        # print("\n" + "=" * 20 + " [Node: Cpu Tool] " + "=" * 20)
        cpu_info = get_cpu_usage(interval=1)
        return {"system_info": {"cpu": cpu_info}}

    def disk_node(self, state: AgentState):
        """磁盘监控节点"""
        # print("\n" + "=" * 20 + " [Node: Disk Tool] " + "=" * 20)
        disk_info = get_disk_usage()
        return {"system_info": {"disk": disk_info}}

    def network_node(self, state: AgentState):
        """网络节点：获取流量、网速和连接"""
        # print("\n" + "=" * 20 + " Network Node "+ "=" * 20)
        data = get_network_general_info(interval=1.0)
        return {"system_info": {"network": data}}

    def memory_node(self, state: AgentState):
        """内存节点：获取详细内存信息"""
        # print("\n" + "=" * 20 + " [Node: Memory Tool] " + "=" * 20)
        data = get_memory_general_info()
        return {"system_info": {"memory": data}}

    def router(self, state: AgentState) -> str:
        """
        [综合路由]
        决定下一步去哪里。
        """
        self.retrieve_router = RetrieveRouter()
        self.llm_arbitrator = LLMArbitrator()
        current_message = state["messages"][-1]["content"].lower()
        # print(f" 路由分析: {current_message}")

        string_match_result = string_match_router(current_message)
        # print(f"字符串匹配结果: {string_match_result}")

        retrieve_category,retrieve_word, retrieve_score = self.retrieve_router.find_best_keyword(current_message)

        # print(f"语义搜索结果: {retrieve_category,retrieve_word} (得分: {retrieve_score:.4f})")

        # 如果语义搜索结果在字符串匹配结果中，或语义搜索非常确定而字符串匹配较弱
        if retrieve_category in string_match_result and retrieve_category is not None:
            # print(f"达成共识: {retrieve_category}")
            return retrieve_category

        # print("结果不同或不确定。调用LLMAbitrator。")
        # 将字符串匹配结果列表传递给LLMAbitrator
        retrieve_result = retrieve_category + retrieve_word + str(retrieve_score)
        current_message = self.llm_arbitrator.arbitrate(current_message, string_match_result, retrieve_result)
        # print(f"LLM决定: '{current_message}'")

        # print(f"最终去: '{current_message}'")
        return current_message