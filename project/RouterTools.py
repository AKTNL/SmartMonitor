import os
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModel
import json
import torch.nn.functional as F
from langchain_ollama import ChatOllama


PROJECT_ROOT = Path(__file__).resolve(strict=False).parent.parent
LOCAL_EMBED_MODEL_PATH = PROJECT_ROOT / "models" / "bge-small-zh-v1.5"
KEYWORD_EMBEDS_PATH = PROJECT_ROOT / "keyword_embeds.pt"
KEYWORD_INDEX_PATH = PROJECT_ROOT / "keyword_index.json"
ARBITRATOR_MODEL_NAME = os.environ.get("ARBITRATOR_MODEL_NAME", "MyQwen3-0.6B:latest")


def string_match_router(message: str) -> str:
    """
    Performs simple string matching to find a category for the message.
    """
    keyword_dict = {
        "cpu": [
            "cpu", "处理器", "负载", "频率", "核心", "主频",
            "计算能力", "上下文切换", "使用率", "线程", "物理核", "逻辑核", "MHz",
            # 来自 JSON 字段及近义词
            "cpu使用率", "每个核心使用率", "逻辑核心数", "物理核心数", "当前CPU频率",
            "系统负载", "上下文切换次数", "CPU频率", "核心使用率", "平均负载", "cpu负载"
        ],
        "memory": [
            "内存", "ram", "swap", "交换分区", "可用内存", "已用内存",
            "内存使用率", "缓存", "缓冲区", "共享内存", "活跃内存", "不活跃内存", "空闲内存剩余量",
            # 来自 JSON 字段及近义词
            "总内存", "可用内存", "已用内存", "空闲内存", "内存占用率", "交换分区总量",
            "交换分区已用", "交换分区空闲", "交换分区使用率", "内存警报", "物理内存",
            "虚拟内存", "RSS", "VMS", "内存状态", "内存健康"
        ],
        "disk": [
            "disk", "磁盘", "挂载", "系统文件", "设备路径", "IO", "读写", "io",
            "分区", "ext4", "xfs", "ntfs", "总容量", "已用容量", "空闲容量", "使用率", "字节数",
            # 来自 JSON 字段及近义词
            "设备", "挂载点", "文件系统类型", "总容量", "已用容量", "空闲容量", "使用率",
            "读取次数", "写入次数", "读取字节", "写入字节", "IO统计", "磁盘IO", "磁盘读写",
            "分区信息", "存储空间", "磁盘健康", "磁盘占用"
        ],
        "process": [
            "进程", "process", "pid", "kill", "杀", "查找", "程序", "高占用",
            "资源占用", "运行状态", "systemd", "chrome", "python", "进程总数",
            # 来自 JSON 字段及近义词
            "高资源占用进程", "进程概览", "进程总数", "CPU使用率", "内存使用", "用户",
            "名称", "状态", "PID", "进程名", "运行用户", "进程状态", "资源消耗",
            "前5高占用", "Top进程", "进程列表", "系统进程"
        ],
        "file": [
            "file", "日志", "路径", "log", "read", "获取", "显示", "目录",
            "大文件", "根目录", "总大小", "文件数", "子目录", "概览",
            # 来自 JSON 字段及近义词
            "目录概览", "文件总数", "子目录总数", "总大小", "概览条目", "大文件列表",
            "路径", "大小", "大小_字节", "文件路径", "文件体积", "最大文件", "占用空间",
            "目录内容", "文件分布", "存储占用"
        ],
        "network": [
            "网络", "network", "ip", "ping", "流量", "网速", "端口", "连接",
            "上传", "下载", "实时网速", "发送", "接收", "包数", "错误", "丢弃",
            "接口", "IPv4", "IPv6", "子网掩码", "广播", "MTU", "全双工", "活跃连接",
            # 来自 JSON 字段及近义词
            "累计流量统计", "实时网速", "网络接口地址", "网络接口状态", "活跃连接",
            "发送字节", "接收字节", "发送包数", "接收包数", "发送错误数", "接收错误数",
            "丢弃包数", "发送速度", "接收速度", "是否开启", "是否全双工", "速度", "接口名称",
            "本地地址", "远程地址", "连接状态", "Socket类型", "网络健康", "带宽使用",
            "网络错误", "丢包", "IP配置", "网络活动"
        ],
        "system_monitor": [
            # 系统层面
            "系统", "监控", "资源", "性能", "卡不卡", "状态", "OpenEuler",

            # 组合监控（场景化）
            "CPU负载和磁盘剩余空间", "内存和CPU使用率", "进程和网络连接",
            "磁盘IO和CPU负载", "内存使用和交换分区", "网络流量和CPU占用",

            # 系统状态检查
            "系统健康状态", "资源使用情况", "整体性能", "运行状况",
            "系统负载", "运行时间", "用户数", "平均负载",

            # 监控命令相关
            "top", "htop", "vmstat", "iostat", "sar", "dstat",
            "性能监控", "实时监控", "资源监控", "系统监控",

            # 问题诊断场景
            "系统卡顿", "响应慢", "速度慢", "延迟高",
            "资源不足", "内存不足", "磁盘满了", "CPU过高",
            "性能瓶颈", "系统瓶颈", "资源瓶颈",

            # 综合指标
            "系统指标", "性能指标", "关键指标", "监控指标",
            "CPU内存磁盘", "CPU内存网络", "系统整体资源",
            "负载情况", "使用情况", "占用情况",

            # 监控面板/概览
            "仪表板", "监控面板", "系统概览", "资源概览",
            "整体视图", "监控视图", "性能视图",

            # 报警相关
            "监控告警", "资源告警", "性能告警", "阈值",
            "告警通知", "监控提醒",

            # 特定工具
            "nmon", "glances", "netdata", "prometheus",
            "grafana", "监控工具", "性能工具",

            # 新增：基于各模块 JSON 字段的综合描述
            "进程总数", "内存使用率", "磁盘使用率", "网络实时速度", "CPU核心使用",
            "大文件位置", "活跃网络连接", "交换分区状态", "系统进程列表", "磁盘IO统计"
        ],
        "simple_chat": [
            "你好", "hello", "hi", "help", "帮助"
        ],
    }
    matched_categories = []
    message_lower = message.lower()
    for category, keywords in keyword_dict.items():
        if any(k in message_lower for k in keywords):
            matched_categories.append(category)

    if not matched_categories:
        return ["simple_chat"]
    return matched_categories


class RetrieveRouter:
    def __init__(self, model_name=None):
        default_model = os.environ.get("LOCAL_MODEL_PATH")
        if not default_model and LOCAL_EMBED_MODEL_PATH.exists():
            default_model = str(LOCAL_EMBED_MODEL_PATH)
        if not default_model:
            default_model = "BAAI/bge-small-zh-v1.5"

        self.model_name = model_name if model_name else default_model
        self.is_local = os.path.exists(self.model_name)
        self.available = False
        self.error = None

        try:
            if not KEYWORD_EMBEDS_PATH.exists() or not KEYWORD_INDEX_PATH.exists():
                raise FileNotFoundError("keyword router resources are missing")

            print(f"DEBUG: RetrieveRouter 正在加载模型: {self.model_name} (本地模式: {self.is_local})")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                local_files_only=self.is_local
            )
            self.model = AutoModel.from_pretrained(
                self.model_name,
                local_files_only=self.is_local
            )
            self.model.eval()

            self.KEYWORD_EMBEDS = torch.load(KEYWORD_EMBEDS_PATH, map_location="cpu")
            with open(KEYWORD_INDEX_PATH, "r", encoding="utf-8") as f:
                self.KEYWORD_INDEX = json.load(f)

            self.available = True
        except Exception as exc:
            self.error = str(exc)
            self.tokenizer = None
            self.model = None
            self.KEYWORD_EMBEDS = None
            self.KEYWORD_INDEX = None
            print(f"WARNING: RetrieveRouter 已禁用: {self.error}")

    def encode(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        emb = outputs.last_hidden_state.mean(dim=1)
        return F.normalize(emb, p=2, dim=1)


    def find_best_keyword(self, sentence: str):
        if not self.available:
            return None, None, None

        sent_emb = self.encode(sentence)  # (1,dim)

        # (1,dim) @ (dim,N) -> (1,N)
        scores = (sent_emb @ self.KEYWORD_EMBEDS.T).squeeze(0)

        best_idx = torch.argmax(scores).item()
        best_score = scores[best_idx].item()

        best_item = self.KEYWORD_INDEX[best_idx]
        return best_item["category"], best_item["word"], best_score


# 4. LLM Arbitrator
class LLMArbitrator:
    """
    Uses an LLM to decide on a routing category when other methods disagree.
    """

    ALLOWED = ["cpu", "memory", "disk", "process", "file", "network", "system_monitor"]

    def __init__(self, model_name=ARBITRATOR_MODEL_NAME):
        self.model = ChatOllama(model=model_name)

    def arbitrate(self, user_input: str, string_match: list, semantic_match: str) -> str:
        # 直接构造prompt模板
        prompt = f"<|im_start|>user\n请从 7 个类别中选一个最合理的类别，只输出类别名称。\n用户原始输入是：{user_input}\n方法1（关键字匹配）结果是：{', '.join(string_match)} \n方法2（语义检索）结果是：{semantic_match}<|im_end|>\n<|im_start|>assistant\n"

        # 直接调用model的invoke方法
        result = self.model.invoke(prompt).content.strip().lower()
        # 处理LLM输出，只保留"think"之后的内容
        # 处理LLM输出，删除"</think>"以及它之前的所有内容
        if "</think>" in result:
            # 分割字符串，取"</think>"之后的部分
            parts = result.split("</think>", 1)
            if len(parts) > 1:
                result = parts[1].strip()
                # 如果结果以换行符开头，去掉开头的换行符
                if result.startswith("\n"):
                    result = result[1:].strip()
        # 如果 LLM 输出不在 allowed 中
        if result not in self.ALLOWED:
            print(f"LLM输出非法: {result},route到system_monitor")
            return "system_monitor"

        return result
