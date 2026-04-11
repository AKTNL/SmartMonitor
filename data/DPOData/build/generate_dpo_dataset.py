import json

# 读取原始数据
with open('../clear_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 定义类别列表，用于生成劣质回答
categories = ["cpu", "memory", "disk", "process", "file", "network", "system_monitor", "simple_chat"]

# 转换函数
def convert_to_dpo_format(item):
    # 拼接 instruction 和 system 字段
    instruction_with_system = f"{item['instruction']}\n{item['system']}"
    
    # 创建劣质回答列表（排除正确答案）
    rejected_options = [cat for cat in categories if cat != item['output']]
    
    dpo_item = {
        "instruction": instruction_with_system,
        "input": item['input'],
        "chosen": item['output'],
        "rejected": ", ".join(rejected_options)
    }
    
    return dpo_item

# 转换所有数据项
dpo_data = [convert_to_dpo_format(item) for item in data]

# 保存为新的JSON文件
with open('dpo_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(dpo_data, f, ensure_ascii=False, indent=2)

print(f"成功转换 {len(dpo_data)} 条数据到DPO格式！")