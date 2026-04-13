import sqlite3
import uuid
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "smartmonitor_history.db"
LEGACY_DB_NAME = "eulermind_history.db"


def _resolve_db_path():
    """优先使用新数据库名，同时兼容旧文件名。"""
    new_path = os.path.join(BASE_DIR, DB_NAME)
    legacy_path = os.path.join(BASE_DIR, LEGACY_DB_NAME)

    if os.path.exists(new_path):
        return new_path
    if os.path.exists(legacy_path):
        return legacy_path
    return new_path


DB_PATH = _resolve_db_path()

def get_connection():
    """获取数据库连接，并设置字典形式返回数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. 会话表 (左侧对话列表)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. 消息表 (右侧聊天记录)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,           -- 'human' 或 'ai'
            content TEXT,        -- 消息文本
            system_info TEXT,    -- 序列化后的 JSON 字符串，保存系统状态
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    conn.commit()
    conn.close()

def create_conversation(title="新对话"):
    """创建一个新对话"""
    conn = get_connection()
    cursor = conn.cursor()
    conv_id = str(uuid.uuid4())
    cursor.execute('INSERT INTO conversations (id, title) VALUES (?, ?)', (conv_id, title))
    conn.commit()
    conn.close()
    return conv_id

def get_all_conversations():
    """获取所有对话列表（按更新时间倒序，最近聊的在最上面）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM conversations ORDER BY updated_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return[dict(row) for row in rows]

def add_message(conversation_id, role, content, system_info=None):
    """
    保存一条消息
    :param system_info: 字典或字符串，如果是字典会自动转为 JSON
    """
    # 处理 system_info 序列化
    if isinstance(system_info, dict):
        system_info_str = json.dumps(system_info, ensure_ascii=False)
    else:
        system_info_str = system_info

    conn = get_connection()
    cursor = conn.cursor()
    msg_id = str(uuid.uuid4())
    
    cursor.execute('''
        INSERT INTO messages (id, conversation_id, role, content, system_info) 
        VALUES (?, ?, ?, ?, ?)
    ''', (msg_id, conversation_id, role, content, system_info_str))
    
    # 更新会话的最后活跃时间
    cursor.execute('UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (conversation_id,))
    
    conn.commit()
    conn.close()

def get_messages(conversation_id):
    """获取某个对话的所有历史消息，并将 system_info 解析回字典"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC', (conversation_id,))
    rows = cursor.fetchall()
    conn.close()
    
    messages =[]
    for row in rows:
        msg = dict(row)
        # 尝试将 JSON 字符串还原为字典
        if msg.get('system_info'):
            try:
                msg['system_info'] = json.loads(msg['system_info'])
            except json.JSONDecodeError:
                pass # 如果解析失败就保留原字符串
        messages.append(msg)
        
    return messages

# 测试代码 (直接运行此文件可测试数据库是否正常工作)
if __name__ == "__main__":
    print("正在初始化数据库...")
    init_db()
    print("数据库初始化完成！")
    
    # 模拟一次测试写入
    conv_id = create_conversation("测试网络查询")
    add_message(conv_id, "human", "我想查看当前的网络连接情况")
    
    mock_system_info = {
        "网络接口状态": "Ethernet开启",
        "活跃连接": "TCP连接",
        "本地地址": "127.0.0.1"
    }
    add_message(conv_id, "ai", "接口Ethernet开启，支持正常通信...", mock_system_info)
    
    print("\n读取测试对话记录:")
    for m in get_messages(conv_id):
        print(f"[{m['role']}] {m['content']}")
        if m['system_info']:
            print(f"  -> 附带系统信息: {m['system_info']}")
