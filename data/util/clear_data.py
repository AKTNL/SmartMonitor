import re
import json

from RouterTools import string_match_router

with open("../LoraData/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


def match(Item):
    user_input_match = re.search(r"用户原始输入是：(.*?)\n方法1", Item["input"])
    string_match_result_match = re.search(r"方法1（关键字匹配）结果是：(.*?)\n方法2", Item["input"])

    user_input = user_input_match.group(1)
    # 将字符串形式的结果转为列表并去除空格
    string_match_result_str = string_match_result_match.group(1)# 提取正则表达式的第一个（）
    string_match_result = [x.strip() for x in string_match_result_str.split(',')] # 这里使用split分开获取到的字符串

    return user_input, string_match_result
def clean_data(data):
    cleaned_data = []
    count=0
    for item in data:
        user_input,string_match_result = match(item)
        computed_string_match_result = string_match_router(user_input)
        is_matched = sorted(computed_string_match_result) == sorted(string_match_result)

        if is_matched:
            cleaned_data.append(item)
            count+=1
        else:
            print("--- 不匹配的数据项 ---")
            print(f"原始输入: {user_input}")
            print(f"JSON中记录的关键字匹配结果: {string_match_result}")
            print(f"string_match_router计算的关键字匹配结果: {computed_string_match_result}")
            print(f"完整数据项: {item}")
            print("----------------------")
    return cleaned_data, count

cleaned_data,count=clean_data(data)

with open("../LoraData/clear_data.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
print(f"已保存：{count}条数据")