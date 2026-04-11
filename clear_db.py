import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eulermind_history.db")

def clear_all_data():
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，无需清理。")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空两张表的数据
    cursor.execute('DELETE FROM messages')
    cursor.execute('DELETE FROM conversations')
    
    conn.commit()
    conn.close()
    print("✅ 所有测试数据已成功清空！")

if __name__ == "__main__":
    clear_all_data()