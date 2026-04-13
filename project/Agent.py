import os
import sys
from pathlib import Path

# 1. 获取项目根目录
current_dir = Path(__file__).resolve(strict=False).parent
project_root = current_dir.parent

# 2. 强制把“当前工作目录”切换到项目根目录
os.chdir(project_root)

# 3. 把项目根目录加入 Python 搜索路径
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

local_model_path = project_root / "models" / "bge-small-zh-v1.5"
if local_model_path.exists():
    os.environ.setdefault("LOCAL_MODEL_PATH", str(local_model_path))
else:
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

CHAT_MODEL_NAME = os.environ.get("SMARTMONITOR_MODEL_NAME", "qwen3:0.6b")

from .AgentGraph import AgentGraph


def main():
    # 1. 初始化 Agent
    model_name = CHAT_MODEL_NAME
    print(f"[INFO] 正在初始化 Agent (模型: {model_name})...")
    
    try:
        graph = AgentGraph(model_name)
        agent = graph.get_graph()
        print("[INFO] 初始化完成。")
        print("[INFO] 提示：输入 'exit', 'quit' 或 'q' 退出程序。")
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        return

    # 2. 进入交互循环
    while True:
        try:
            # 获取用户输入
            # flush=True 确保提示符立即显示
            user_input = input("\n请输入指令: ").strip()

            # 检查退出条件
            if user_input.lower() in ["exit", "quit", "q"]:
                print("再见。")
                break
            
            # 处理空输入
            if not user_input:
                continue

            # 3. 动态构建 state
            # 注意：如果你希望 AI 记住上下文，这里需要维护一个 messages 列表
            # 目前按你原代码逻辑，每次都是新的对话
            state = {
                "messages": [{"role": "human", "content": user_input}],
                "system_info": None
            }

            print("[INFO] 正在思考与执行工具...")

            # 4. 调用 Agent
            result = agent.invoke(state)
            
            # 5. 输出结果
            print("\nAI 回复:")
            print("-" * 50)
            # 获取最后一条消息（AI 的回复）
            ai_response = result["messages"][-1]["content"]
            print(ai_response)
            print("-" * 50)

        except KeyboardInterrupt:
            # 捕获 Ctrl+C
            print("\n\n[INFO] 用户强制中断，正在退出...")
            break
        except Exception as e:
            print(f"\n[ERROR] 运行出错: {e}")

if __name__ == "__main__":
    main()
