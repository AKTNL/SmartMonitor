import sys
import os
import site
import platform

# 1. 获取当前脚本的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 强制把“当前工作目录”切换到脚本所在目录
os.chdir(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

local_model_path = os.path.join(current_dir, "models", "bge-small-zh-v1.5")
if os.path.exists(local_model_path):
    # 告诉环境变量或者你的 AgentGraph 优先读这里
    os.environ.setdefault("LOCAL_MODEL_PATH", local_model_path)
    print(f"[INFO] 已定位离线模型: {local_model_path}")
else:
    # 如果没找到离线版，再尝试走镜像站在线下
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    print("[INFO] 未发现离线模型，将尝试在线连接镜像站")

CHAT_MODEL_NAME = os.environ.get("SMARTMONITOR_MODEL_NAME", "qwen3:0.6b")


def _configure_windows_qt_runtime():
    """在 Windows 上为 Qt 补充 DLL 搜索路径。"""
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return []

    handles = []
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    system32_dir = os.path.join(system_root, "System32")
    if os.path.isdir(system32_dir):
        handles.append(os.add_dll_directory(system32_dir))

    site_roots = []
    for getter in (site.getsitepackages, site.getusersitepackages):
        try:
            value = getter()
        except Exception:
            continue

        if isinstance(value, str):
            site_roots.append(value)
        else:
            site_roots.extend(value)

    qt_candidates = []
    for root in site_roots:
        candidate = os.path.join(root, "PyQt6", "Qt6", "bin")
        if os.path.isdir(candidate) and candidate not in qt_candidates:
            qt_candidates.append(candidate)

    for candidate in qt_candidates:
        handles.append(os.add_dll_directory(candidate))

    return handles


_QT_DLL_DIR_HANDLES = _configure_windows_qt_runtime()

# 1. 设置环境变量 (必须在导入 transformers/langchain 之前设置)
# os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import database

# 根据目录结构，从 project 包中导入 AgentGraph
try:
    from project.AgentGraph import AgentGraph
except ImportError as e:
    print("[ERROR] 导入错误: 找不到 project 模块。")
    print("请确保你在项目的'根目录'下运行此脚本 (能看到 pyproject.toml 的那个目录)")
    print(f"详细报错: {e}")
    sys.exit(1)


# 后台工作线程：负责跑 AI 模型，防止界面卡死
class AIWorker(QThread):
    response_signal = pyqtSignal(str, object) #发送 AI 回复内容
    status_signal = pyqtSignal(str) # 发送当前状态（如：思考中...）

    # 全局变量：保持 Agent 实例，避免每次对话都重新加载模型
    agent_instance = None

    def __init__(self, user_text, conversation_id):
        super().__init__()
        self.user_text = user_text
        self.conversation_id = conversation_id

    def run(self):
        # --- 1. 初始化阶段 (只在第一次运行时执行) ---
        if AIWorker.agent_instance is None:
            self.status_signal.emit(f"🔄 正在初始化 Agent (模型: {CHAT_MODEL_NAME})...")
            try:
                # 对应 Agent.py 里的初始化逻辑
                model_name = CHAT_MODEL_NAME
                graph = AgentGraph(model_name)
                AIWorker.agent_instance = graph.get_graph()
                self.status_signal.emit("✅ 初始化完成！")
            except Exception as e:
                self.response_signal.emit(f"❌ 初始化失败: {str(e)}", None)
                return
        
        # --- 2. 推理阶段 ---
        self.status_signal.emit("⏳ 正在思考与执行工具...")
        try:
            #从数据库拉取当前对话的历史记录，喂给大模型
            history = database.get_messages(self.conversation_id)
            messages_for_ai =[]
            for msg in history:
                # 把历史记录构造成 Agent 需要的格式
                messages_for_ai.append({"role": msg['role'], "content": msg['content']})

            # 构造 state，对应 Agent.py 里的逻辑
            state = {
                "messages": messages_for_ai,
                "system_info": None
            }

            # 调用 Agent
            result = AIWorker.agent_instance.invoke(state)

            # 获取最后一条消息（AI 的回复）
            ai_response = result["messages"][-1]["content"]

            system_info = result.get("system_info", None) # 提取系统状态

            # 发送结果回界面
            self.response_signal.emit(ai_response, system_info)

        except Exception as e:
            self.response_signal.emit(f"❌ 运行出错: {str(e)}", None)


# 图形界面代码 (GUI)
class HoverButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(90, 42)
        self._ani = QVariantAnimation(self)
        self._ani.setDuration(200)
        self._ani.setEasingCurve(QEasingCurve.Type.OutBack)
        self._ani.valueChanged.connect(self._update_geometry)
        self.setStyleSheet("""
            QPushButton {
                background: #3B82F6; color: white; border-radius: 12px;
                font-weight: bold; font-size: 14px; border: none;
            }
            QPushButton:hover { background: #2563EB; }
            QPushButton:disabled { background: #1E293B; color: #64748B; }
        """)

    def _update_geometry(self, v):
        self.setFixedSize(int(90 + v*10), int(42 + v*4))

    def enterEvent(self, event):
        if self.isEnabled():
            self._ani.setStartValue(0); self._ani.setEndValue(1); self._ani.start()
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def leaveEvent(self, event):
        self._ani.setStartValue(1); self._ani.setEndValue(0); self._ani.start()

class ModernChatBubble(QFrame):
    def __init__(self, text, is_user=True):
        super().__init__()
        self.is_user = is_user
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5) 
        
        # 用户消息直接显示内容，AI消息初始为空（由打字机填充）
        display_text = text # if is_user else ""
        self.bubble = QLabel(display_text)
        self.bubble.setWordWrap(True)
        self.bubble.setMaximumWidth(600) 
        self.bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if platform.system() == "Windows":
            font_family = "Microsoft YaHei UI"
        elif platform.system() == "Darwin":
            font_family = "PingFang SC"
        else:
            font_family = "Sans Serif"
        self.bubble.setFont(QFont(font_family, 10))

        style = "padding: 12px 18px; border-radius: 15px;"
        if is_user:
            self.bubble.setStyleSheet(f"{style} background: #2563EB; color: white; border-bottom-right-radius: 2px;")
            layout.addStretch(1)
            layout.addWidget(self.bubble)
        else:
            self.bubble.setStyleSheet(f"{style} background: rgba(255, 255, 255, 0.1); color: #F1F5F9; border: 1px solid rgba(255, 255, 255, 0.1); border-bottom-left-radius: 2px;")
            layout.addWidget(self.bubble)
            layout.addStretch(1)

    def update_text(self, text):
        """供打字机调用的更新函数"""
        self.bubble.setText(text)

# --- 主窗口 ---
class EulerMindWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 初始化数据库
        database.init_db()
        self.current_conversation_id = None
        
        # 打字机相关状态
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._on_typing_tick)
        self.full_response = ""
        self.current_char_idx = 0
        self.current_ai_bubble = None

        self.init_ui()
        self.add_glow_effect()

        # 启动时加载左侧对话列表
        self.load_conversations()

    def init_ui(self):
        self.resize(1150, 750)
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setGeometry(15, 15, 1120, 720)
        self.main_container.setStyleSheet("#MainContainer { background: #0F172A; border-radius: 25px; border: 1px solid rgba(255,255,255,0.1); }")

        layout = QVBoxLayout(self.main_container)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("SmartMonitor")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header.addWidget(self.title_label); header.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("QPushButton{background:transparent; color:#64748B; font-size:18px;} QPushButton:hover{color:#EF4444;}")
        header.addWidget(close_btn)
        layout.addLayout(header)

        # 水平布局：左侧历史列表 + 右侧聊天区
        content_layout = QHBoxLayout()

        # --- 左侧：侧边栏 ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("background: rgba(255,255,255,0.02); border-radius: 15px;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        self.new_chat_btn = QPushButton("＋ 新建对话")
        self.new_chat_btn.setFixedHeight(40)
        self.new_chat_btn.setStyleSheet("""
            QPushButton { background: #3B82F6; color: white; border-radius: 10px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background: #2563EB; }
        """)
        self.new_chat_btn.clicked.connect(self.start_new_conversation)
        sidebar_layout.addWidget(self.new_chat_btn)
        
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; color: #CBD5E1; font-size: 13px; outline: none; }
            QListWidget::item { padding: 12px; border-radius: 8px; margin-bottom: 5px; }
            QListWidget::item:hover { background: rgba(255,255,255,0.05); }
            QListWidget::item:selected { background: rgba(59,130,246,0.3); color: white; border: 1px solid #3B82F6; }
        """)
        self.chat_list.itemClicked.connect(self.switch_conversation)
        sidebar_layout.addWidget(self.chat_list)
        
        content_layout.addWidget(self.sidebar)

        # --- 右侧：聊天区域 ---
        chat_area = QWidget()
        chat_area_layout = QVBoxLayout(chat_area)
        chat_area_layout.setContentsMargins(15, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background:transparent; border:none;")
        self.scroll_content = QWidget()
        self.chat_layout = QVBoxLayout(self.scroll_content)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        chat_area_layout.addWidget(self.scroll_area)

        input_container = QFrame()
        input_container.setFixedHeight(70)
        input_container.setStyleSheet("background:rgba(255,255,255,0.05); border-radius:15px; border:1px solid rgba(255,255,255,0.1);")
        input_layout = QHBoxLayout(input_container)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("键入指令...")
        self.input_field.setStyleSheet("background:transparent; border:none; color:white; font-size:14px;")
        self.input_field.returnPressed.connect(self.handle_send)
        
        self.send_btn = HoverButton("发送")
        self.send_btn.clicked.connect(self.handle_send)
        
        input_layout.addWidget(self.input_field); input_layout.addWidget(self.send_btn)
        chat_area_layout.addWidget(input_container)
        
        content_layout.addWidget(chat_area)
        layout.addLayout(content_layout)

        # Status Bar
        footer = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_text = QLabel("系统就绪")
        self.status_text.setStyleSheet("color:#64748B; font-size:12px;")
        footer.addWidget(self.status_dot); footer.addWidget(self.status_text)
        layout.addLayout(footer)

    def add_glow_effect(self):
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(20); glow.setColor(QColor(59, 130, 246, 120)); glow.setOffset(0,0)
        self.main_container.setGraphicsEffect(glow)
        self.glow_ani = QPropertyAnimation(glow, b"blurRadius")
        self.glow_ani.setDuration(1500); self.glow_ani.setStartValue(15); self.glow_ani.setEndValue(30)
        self.glow_ani.setEasingCurve(QEasingCurve.Type.InOutSine); self.glow_ani.setLoopCount(-1); self.glow_ani.start()

    def load_conversations(self):
        """加载左侧列表"""
        self.chat_list.clear()
        convs = database.get_all_conversations()
        
        if not convs:
            self.start_new_conversation()
            return
            
        for conv in convs:
            item = QListWidgetItem(conv['title'])
            item.setData(Qt.ItemDataRole.UserRole, conv['id'])
            self.chat_list.addItem(item)
            
        # 默认选中第一个
        if self.current_conversation_id is None:
            self.current_conversation_id = convs[0]['id']
            self.chat_list.setCurrentRow(0)
            self.load_chat_history()

    def start_new_conversation(self):
        """新建对话"""
        new_id = database.create_conversation("新对话")
        self.current_conversation_id = new_id
        self.load_conversations()
        self.clear_chat()

    def switch_conversation(self, item):
        """点击列表切换对话"""
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        if conv_id == self.current_conversation_id:
            return
        self.current_conversation_id = conv_id
        self.load_chat_history()

    def load_chat_history(self):
        """加载右侧聊天记录"""
        self.clear_chat()
        messages = database.get_messages(self.current_conversation_id)
        for msg in messages:
            is_user = (msg['role'] == 'human')
            self.chat_layout.addWidget(ModernChatBubble(msg['content'], is_user=is_user))
        self.smooth_scroll_to_bottom()

    def clear_chat(self):
        """清空聊天面板"""
        while self.chat_layout.count():
            child = self.chat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def handle_send(self):
        text = self.input_field.text().strip()
        if not text or self.typing_timer.isActive(): return

        # 将用户消息存入数据库
        database.add_message(self.current_conversation_id, "human", text)
        
        # 1. 界面反馈
        self.chat_layout.addWidget(ModernChatBubble(text, is_user=True))
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self.smooth_scroll_to_bottom()
        
        # 2. 启动后台
        self.update_status("⏳ 正在思考...", "#F59E0B")
        self.worker = AIWorker(text, self.current_conversation_id)
        self.worker.response_signal.connect(self.start_typewriter) 
        self.worker.status_signal.connect(lambda s: self.update_status(s, "#F59E0B"))
        self.worker.start()

    def start_typewriter(self, full_text, system_info):
        """初始化打字机效果"""

        # 将 AI 的回复以及 system_info 存入数据库
        database.add_message(self.current_conversation_id, "ai", full_text, system_info)
        
        self.update_status("✍️ 正在回复...", "#3B82F6")
        self.full_response = full_text
        self.current_char_idx = 0
        
        # 创建一个空的 AI 气泡
        self.current_ai_bubble = ModernChatBubble("", is_user=False)
        self.chat_layout.addWidget(self.current_ai_bubble)
        
        # 启动定时器 (每 25ms 打印一个字)
        self.typing_timer.start(25)

    def _on_typing_tick(self):
        """打字机每一帧的动作"""
        if self.current_char_idx < len(self.full_response):
            self.current_char_idx += 1
            displayed = self.full_response[:self.current_char_idx]
            self.current_ai_bubble.update_text(displayed)
            self.smooth_scroll_to_bottom()
        else:
            self.typing_timer.stop()
            self.finish_interaction()

    def finish_interaction(self):
        """结束对话状态"""
        self.update_status("✅ 系统就绪", "#10B981")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

        if self.chat_list.currentItem() and self.chat_list.currentItem().text() == "新对话":
            pass

    def smooth_scroll_to_bottom(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.maximum())

    def update_status(self, text, color):
        self.status_text.setText(text)
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 14px; background: transparent;")

    # 窗口拖动逻辑
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EulerMindWindow()
    win.show()
    sys.exit(app.exec())
