import random
from RouterTools import string_match_router
import torch
from transformers import AutoTokenizer, AutoModel
import json
import torch.nn.functional as F
class RetrieveRouter:
    def __init__(self, model_name="BAAI/bge-small-zh-v1.5"):
        # 初始化模型和分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

        # 加载预计算的嵌入向量和索引
        self.KEYWORD_EMBEDS = torch.load("keyword_embeds.pt")
        with open("keyword_index.json", "r", encoding="utf-8") as f:
            self.KEYWORD_INDEX = json.load(f)

    def encode(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        emb = outputs.last_hidden_state.mean(dim=1)
        return F.normalize(emb, p=2, dim=1)


    def find_best_keyword(self, sentence: str):
        sent_emb = self.encode(sentence)  # (1,dim)

        # (1,dim) @ (dim,N) -> (1,N)
        scores = (sent_emb @ self.KEYWORD_EMBEDS.T).squeeze(0)

        best_idx = torch.argmax(scores).item()
        best_score = scores[best_idx].item()

        best_item = self.KEYWORD_INDEX[best_idx]
        return best_item["category"], best_item["word"], best_score

# 关键词字典
keyword_dict = {
    "cpu": [
        "cpu", "处理器", "负载", "load", "频率", "核心", "core", "主频",
        "计算能力", "上下文切换", "使用率", "线程", "物理核", "逻辑核", "MHz",
        # 来自 JSON 字段及近义词
        "cpu使用率", "每个核心使用率", "逻辑核心数", "物理核心数", "当前CPU频率",
        "系统负载", "上下文切换次数", "CPU频率", "核心使用率", "平均负载", "cpu负载"
    ],
    "memory": [
        "内存", "memory", "ram", "swap", "交换分区", "可用内存", "已用内存",
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

def generate_single_category_sentences():
    """为每个关键词生成示例句子"""
    sentences = []
    
    # 为每个类别生成句子
    for category, keywords in keyword_dict.items():
        if category == "simple_chat":
            # 对于简单聊天，直接添加固定句子
            sentences.extend([
                "你好",
                "help",
                "帮助我一下",
                "hi",
                "hello"
            ])
            continue
            
        # 为每个关键词生成1-3个句子
        for keyword in keywords[:min(len(keywords), 20)]:  # 限制每个类别最多20个关键词
            num_sentences = random.randint(1, 3)
            for _ in range(num_sentences):
                templates = [
                    f"我想查看{keyword}的信息",
                    f"请告诉我关于{keyword}的情况",
                    f"我需要检查{keyword}",
                    f"显示{keyword}的状态",
                    f"查询{keyword}的使用情况",
                    f"获取{keyword}的详细信息",
                    f"我想了解{keyword}"
                ]
                sentence = random.choice(templates)
                sentences.append(sentence)
                
    return sentences

def generate_cross_category_sentences():
    """生成跨类别的句子"""
    cross_sentences = []
    
    # 定义一些组合模式
    combinations = [
        ("memory", "disk"),
        ("cpu", "memory"),
        ("network", "process"),
        ("file", "disk"),
        ("cpu", "disk", "memory"),
        ("network", "cpu"),
        ("process", "memory"),
        ("cpu", "network"),
        ("file", "memory"),
        ("disk", "network"),
        ("cpu", "process"),
        ("file", "process"),
        ("cpu", "file"),
        ("memory", "network"),
        ("disk", "process"),
        ("cpu", "disk", "network"),
        ("file", "network", "memory"),
        ("process", "disk", "network"),
        ("cpu", "file", "process"),
        ("memory", "disk", "network", "process"),
        ("cpu", "memory", "file", "network"),
        ("system_monitor", "cpu"),
        ("system_monitor", "memory"),
        ("system_monitor", "disk"),
        ("system_monitor", "process"),
        ("system_monitor", "file"),
        ("system_monitor", "network"),
        ("cpu", "disk", "file"),
        ("memory", "process", "network"),
        ("disk", "file", "process"),
        ("network", "file", "cpu"),
        ("process", "memory", "disk"),
        ("file", "cpu", "network"),
        ("disk", "memory", "process"),
        ("network", "disk", "file"),
        ("cpu", "process", "file"),
        ("memory", "network", "cpu"),
        ("disk", "cpu", "process"),
        ("file", "disk", "network"),
        ("process", "file", "memory"),
        ("cpu", "network", "disk"),
        ("memory", "file", "cpu"),
        ("disk", "network", "memory"),
        ("process", "cpu", "file"),
        ("file", "process", "disk"),
        ("network", "memory", "file"),
        ("cpu", "disk", "process", "file"),
        ("memory", "network", "process", "file"),
        ("disk", "cpu", "network", "file"),
        ("process", "memory", "cpu", "file"),
        ("file", "disk", "memory", "cpu"),
        ("network", "process", "disk", "cpu"),
        ("system_monitor", "cpu", "memory"),
        ("system_monitor", "disk", "network"),
        ("system_monitor", "process", "file"),
        ("system_monitor", "cpu", "disk", "memory"),
        ("system_monitor", "network", "process", "file")
    ]
    
    for combo in combinations:
        # 获取组合中的关键词
        keywords_list = [random.choice(keyword_dict[cat]) for cat in combo]
        
        # 创建跨类别句子模板
        templates = [
            f"我想同时查看{'和'.join(keywords_list)}的信息",
            f"请告诉我{', '.join(keywords_list)}的使用情况",
            f"检查一下{', '.join(keywords_list)}的状态",
            f"我需要了解{', '.join(keywords_list)}的详细信息",
            f"显示{', '.join(keywords_list)}的当前状态"
        ]
        
        # 为每个模板添加句子
        for template in templates:
            cross_sentences.append(template)
            
    return cross_sentences

def create_dataset_entry(user_input):
    """为单个用户输入创建数据集条目"""
    # 获取字符串匹配结果
    string_match_result = string_match_router(user_input)
    router = RetrieveRouter()
    # 注意：由于缺少必要的模型文件，我们无法执行语义检索
    # 在实际应用中，你需要实现完整的Semantic_Router
    retrieve_category,retrieve_word, retrieve_score = router.find_best_keyword(user_input)  # 占位符
    # 根据规则确定正确输出
    output = ""
    if len(string_match_result) > 1:
        # 多个类别匹配，选择system_monitor
        output = "system_monitor"
    elif len(string_match_result) == 1:
        # 单个类别匹配
        output = string_match_result[0]
    else:
        # 没有匹配项，默认为simple_chat
        output = "simple_chat"
    
    # 构造数据条目
    entry = {
        "instruction": "请从 7 个类别中选一个最合理的类别，只输出类别名称。",
        "input": f"用户原始输入是：{user_input}\n方法1（关键字匹配）结果是：{', '.join(string_match_result)} \n方法2（语义检索）结果是：{retrieve_category}",
        "output": output,
        "system": "你是一名智能路由决策器。你必须从下面类别中选择一个，并且只能输出类别名称：cpu, memory, disk, process, file, network, system_monitor,simple_chat\\n不要输出多余的字、句子、解释、标点、空格。只输出一个类别。如果有多个类别都符合,比如human说的关键字匹配和语义检索的结果包含多个类别，选择system_monitor。",
        "history": []
    }
    
    return entry

def main():
    # 生成单类别句子
    single_category_sentences = generate_single_category_sentences()
    print(f"Generated {len(single_category_sentences)} single-category sentences")
    
    # 生成跨类别句子
    cross_category_sentences = generate_cross_category_sentences()
    print(f"Generated {len(cross_category_sentences)} cross-category sentences")
    
    # 合并所有句子
    all_sentences = single_category_sentences + cross_category_sentences
    print(f"Total sentences: {len(all_sentences)}")
    
    # 创建数据集
    dataset = []
    for sentence in all_sentences:
        entry = create_dataset_entry(sentence)
        dataset.append(entry)
    
    # 保存句子到sentence.json
    with open("../../sentence.json", "w", encoding="utf-8") as f:
        json.dump(all_sentences, f, ensure_ascii=False, indent=2)
    
    # 保存数据集到data.json
    with open("../data.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"Dataset saved with {len(dataset)} entries")

if __name__ == "__main__":
    main()