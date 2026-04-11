from langgraph.graph import StateGraph, END
from .AgentState import AgentState
from .AgentNode import AgentNode


class AgentGraph:
    def __init__(self, model_name: str):
        self.agent_node = AgentNode(model_name)
        self.graph = StateGraph(AgentState)

        self.graph.add_node("start", self.agent_node.start_node)
        self.graph.add_node("system_monitor", self.agent_node.system_monitor_node)
        self.graph.add_node("analysis", self.agent_node.analysis_node)
        self.graph.add_node("simple_chat", self.agent_node.simple_chat_node)

        self.graph.add_node("process", self.agent_node.process_node)

        self.graph.add_node("cpu", self.agent_node.cpu_node)
        self.graph.add_node("disk", self.agent_node.disk_node)
        self.graph.add_node("file", self.agent_node.file_node)

        self.graph.add_node("network", self.agent_node.network_node)
        self.graph.add_node("memory", self.agent_node.memory_node)

        self.graph.set_entry_point("start")

        self.graph.add_conditional_edges(
            "start",
            self.agent_node.router,
            {
                "system_monitor": "system_monitor",
                "simple_chat": "simple_chat",
                "process": "process",

                "cpu": "cpu",
                "disk": "disk",
                "file": "file",

                "network": "network",
                "memory": "memory"
            }
        )

        self.graph.add_edge("cpu", "analysis")
        self.graph.add_edge("disk", "analysis")
        self.graph.add_edge("file", "analysis")

        self.graph.add_edge("process", "analysis")
        self.graph.add_edge("network", "analysis")
        self.graph.add_edge("memory", "analysis")

        self.graph.add_edge("system_monitor", "analysis")

        self.graph.add_edge("analysis", END)
        self.graph.add_edge("simple_chat", END)

        self.app = self.graph.compile()

    def get_graph(self):
        return self.app