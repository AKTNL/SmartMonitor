import torch
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F
import json
import os

tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-zh-v1.5")
model = AutoModel.from_pretrained("BAAI/bge-small-zh-v1.5")

def encode(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    emb = outputs.last_hidden_state.mean(dim=1)
    return F.normalize(emb, p=2, dim=1).squeeze(0)   # shape (dim,)

# 你的 KEYWORDS
KEYWORDS = {
    "cpu": [
        "cpu", "处理器", "负载", "load", "频率", "核心", "core", "主频",
        "计算能力", "上下文切换", "使用率", "线程", "物理核", "逻辑核", "MHz"
    ],
    "memory": [
        "内存", "memory", "ram", "swap", "交换分区", "可用内存", "已用内存",
        "内存使用率", "缓存", "缓冲区", "共享内存", "活跃内存", "不活跃内存","空闲内存剩余量"
    ],
    "disk": [
        "disk", "磁盘", "挂载", "系统文件", "设备路径", "IO", "读写", "io",
        "分区", "ext4", "xfs", "ntfs", "总容量", "已用容量", "空闲容量", "使用率","写入字节","读取字节"
    ],
    "process": [
        "进程", "process", "pid", "kill", "杀", "查找", "程序", "高占用",
        "资源占用", "运行状态", "systemd", "chrome", "python", "进程总数"
    ],
    "file": [
        "file", "日志", "路径", "log", "read", "获取", "显示", "目录",
        "大文件", "根目录", "总大小", "文件数", "子目录", "概览","大文件字节数"
    ],
    "network": [
        "网络", "network", "ip", "ping", "流量", "网速", "端口", "连接",
        "上传", "下载", "实时网速", "发送", "接收", "包数", "错误", "丢弃",
        "接口", "IPv4", "IPv6", "子网掩码", "广播", "MTU", "全双工", "活跃连接"
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
        "grafana", "监控工具", "性能工具"

    ],
    "simple_chat": [
        "你好", "hello", "hi", "help", "帮助"
    ],
}

SAVE_PATH = "../../keyword_embeds.pt"
META_PATH = "../../keyword_index.json"

def build_and_save_keyword_embeddings():
    keyword_embeds = []
    keyword_meta = []    # 每条 embedding 对应的 (category, keyword)

    print("开始计算所有关键词 embedding ...")

    for category, words in KEYWORDS.items():
        for word in words:
            emb = encode(word)
            keyword_embeds.append(emb)
            keyword_meta.append({"category": category, "word": word})

    keyword_embeds = torch.stack(keyword_embeds)   # shape = (N, dim)

    torch.save(keyword_embeds, SAVE_PATH)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(keyword_meta, f, ensure_ascii=False, indent=2)

    print(f"已保存：{SAVE_PATH}, {META_PATH}")

# 只需运行一次
if __name__ == "__main__":
    build_and_save_keyword_embeddings()
