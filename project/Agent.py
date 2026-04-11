from .AgentGraph import AgentGraph
import os
import sys

# 1. 获取当前脚本的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 强制把“当前工作目录”切换到脚本所在目录
os.chdir(current_dir)
# 3. 把这个目录加入 Python 搜索路径
sys.path.append(current_dir)
def main():
    # 1. 初始化 Agent
    model_name = "qwen3:0.6b"
    print(f"🔄 正在初始化 Agent (模型: {model_name})...")
    
    try:
        graph = AgentGraph(model_name)
        agent = graph.get_graph()
        print("✅ 初始化完成！")
        print("💡 提示：输入 'exit', 'quit' 或 'q' 退出程序。")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 2. 进入交互循环
    while True:
        try:
            # 获取用户输入
            # flush=True 确保提示符立即显示
            user_input = input("\n👉 请输入指令: ").strip()

            # 检查退出条件
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 再见！")
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

            print("⏳ 正在思考与执行工具...")

            # 4. 调用 Agent
            result = agent.invoke(state)
            
            # 5. 输出结果
            print("\n🤖 AI 回复:")
            print("-" * 50)
            # 获取最后一条消息（AI 的回复）
            ai_response = result["messages"][-1]["content"]
            print(ai_response)
            print("-" * 50)

        except KeyboardInterrupt:
            # 捕获 Ctrl+C
            print("\n\n🛑 用户强制中断，正在退出...")
            break
        except Exception as e:
            print(f"\n❌ 运行出错: {e}")

if __name__ == "__main__":
    main()