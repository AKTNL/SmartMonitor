from typing import TypedDict, List, Optional
class AgentState(TypedDict):
    messages: List[dict]
    system_info: Optional[dict]  # 存储系统信息
