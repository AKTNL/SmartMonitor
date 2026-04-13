import os
import time
import platform
from pathlib import Path
import re

def _bytes_to_human(n):
    """内部工具：字节转人类可读格式"""
    symbols = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i * 10)
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f %s' % (value, s)
    return "%s B" % n


def _resolve_target_path(raw_path: str, base_dir: str) -> tuple[str | None, str | None]:
    """将用户输入解析为 base_dir 内的安全绝对路径。"""
    base_path = Path(base_dir).resolve(strict=False)
    candidate = Path(raw_path)

    if not candidate.is_absolute():
        candidate = base_path / candidate

    candidate = candidate.resolve(strict=False)

    try:
        candidate.relative_to(base_path)
    except ValueError:
        return None, f"路径非法，禁止访问 {base_path} 以外的区域"

    if not candidate.exists():
        return None, f"目标不存在: {candidate}"

    return str(candidate), None

def search_files_by_name(directory: str, keyword: str, limit: int = 10) -> dict:
    """
    递归搜索文件名包含 keyword 的文件
    """
    if not os.path.exists(directory):
        return {"状态": "error", "信息": f"目录不存在: {directory}"}

    found_files = []

    try:
        # 为了防止全盘扫描卡死，限制扫描深度或数量
        file_scanned_count = 0

        for root, dirs, files in os.walk(directory):
            # 简单的深度保护：如果路径过深，跳过
            if root.count(os.sep) - directory.count(os.sep) > 5:
                continue

            for name in files:
                # 核心逻辑：关键词匹配 (忽略大小写)
                if keyword.lower() in name.lower():
                    filepath = os.path.join(root, name)
                    try:
                        size = os.path.getsize(filepath)
                        found_files.append({
                            "文件名": name,
                            "路径": filepath,
                            "大小": _bytes_to_human(size)
                        })
                    except:
                        pass
                
                file_scanned_count += 1
                if file_scanned_count > 20000: # 扫描过多文件强制停止
                    break
            
            if len(found_files) >= limit:
                break
            if file_scanned_count > 20000:
                break
                
    except Exception as e:
        return {"状态": "error", "信息": str(e)}

    return {
        "状态": "success",
        "搜索关键词": keyword,
        "搜索结果": found_files if found_files else "未找到匹配的文件"
    }

def get_file_example_info(directory: str = None) -> dict:
    """
    获取文件系统概览信息，包含目录统计和大文件列表。
    符合 AgentState 要求的中文 JSON 格式。
    
    Args:
        directory (str): 要扫描的根目录。默认为系统根目录 (Linux: /, Windows: C:/)
    """
    # 1. 确定扫描目录
    if directory is None:
        if platform.system() == "Windows":
            directory = "C:/" 
        else:
            directory = "/"

    if not os.path.exists(directory):
        return {"状态": "error", "信息": f"目录不存在: {directory}"}
    
    if os.path.isfile(directory):
        return get_file_info(directory)

    # --- 功能 1: 目录内容概览 ---
    total_files = 0
    total_subdirs = 0
    total_size_bytes = 0
    overview_entries = []
    
    # 获取第一层概览 (类似 ls -lh)
    try:
        with os.scandir(directory) as it:
            count = 0
            for entry in it:
                # 统计数量
                if entry.is_dir():
                    total_subdirs += 1
                    name = f"{entry.name}/"
                    type_tag = "DIR"
                else:
                    total_files += 1
                    name = entry.name
                    try:
                        size = entry.stat().st_size
                        total_size_bytes += size
                        type_tag = _bytes_to_human(size)
                    except:
                        type_tag = "Unknown"

                # 记录前 10 个条目用于概览
                if count < 10:
                    overview_entries.append(f"{name:<30} | {type_tag}")
                    count += 1
    except PermissionError:
        return {"状态": "error", "信息": "无权访问该目录"}
    
    # --- 功能 2: 查找大文件 (Top 5) ---
    large_files_list = []

    # 限制：为了不让 Agent 卡死，只扫描前 5000 个文件或者只扫 2 层深度
    scanned_files = []
    try:
        file_count = 0
        # 仅遍历 3 层深度以保证速度
        start_level = directory.count(os.sep)
        
        for root, dirs, files in os.walk(directory):
            current_level = root.count(os.sep)
            if current_level - start_level > 3: 
                continue # 超过3层就不扫了
                
            for name in files:
                try:
                    filepath = os.path.join(root, name)
                    size = os.path.getsize(filepath)
                    scanned_files.append((filepath, size))
                    file_count += 1
                    if file_count > 10000: # 强制截断防止卡死
                        break
                except:
                    continue
            if file_count > 10000:
                break
                
        # 排序取 Top 3
        scanned_files.sort(key=lambda x: x[1], reverse=True)
        for path, size in scanned_files[:3]:
            large_files_list.append({
                "路径": path,
                "大小": _bytes_to_human(size),
                "大小_字节": size
            })
            
    except Exception as e:
        pass # 忽略扫描错误

    # --- 组装最终 JSON ---
    return {
        "状态": "success",
        "目录概览": {
            "目录": directory,
            "文件总数": total_files, # 注意：这里只统计了第一层，全量统计太慢
            "子目录总数": total_subdirs,
            "总大小": _bytes_to_human(total_size_bytes),
            "概览条目": overview_entries
        },
        "大文件列表": large_files_list
    }

def get_file_info(file_path: str) -> dict:
    """
    获取单个文件的详细属性
    兼容 Windows 和 Linux
    """
    try:
        p = Path(file_path)
        if not p.exists():
            return {"error": f"文件不存在：{file_path}"}
        
        stat = p.stat()
        
        # 权限处理：Windows 上 st_mode 可能不准确，但不影响运行
        mode_str = oct(stat.st_mode)[-3:]
        
        # 用户ID处理：Windows 上 st_uid 通常为 0，Linux 上才有用
        uid = stat.st_uid if platform.system() != "Windows" else 0

        return {
            "状态": "success",
            "文件名": p.name,
            "路径": str(p.absolute()),
            "大小": _bytes_to_human(stat.st_size),
            "修改时间": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
            "权限": mode_str
        }
    except Exception as e:
        return {"状态": "error", "信息": str(e)}

def read_file_content(file_path: str, lines: int = 50, position: str = 'tail') -> dict:
    """
    安全读取文件内容
    优化：增加了文件大小检查，防止读取超大文件导致内存溢出
    """
    if not os.path.exists(file_path):
        return {"error": f"文件不存在: {file_path}"}
    
    # 1. 检查是不是目录
    if os.path.isdir(file_path):
        return {"error": "这是一个目录，无法读取内容。请使用'列出目录'功能。"}

    # 2. 检查二进制文件后缀
    if file_path.lower().endswith(('.exe', '.dll', '.so', '.bin', '.tar', '.gz', '.zip', '.pyc', '.iso')):
        return {"error": "不支持读取二进制/压缩文件"}

    # 3. 【关键安全检查】文件过大保护
    # 如果文件超过 50MB，禁止使用 readlines() 全量加载，防止内存爆炸
    file_size = os.path.getsize(file_path)
    if file_size > 50 * 1024 * 1024: # 50MB
        return {"error": f"文件过大 ({_bytes_to_human(file_size)})，为了安全禁止直接读取。请尝试获取文件属性。"}

     # 4. 检查是否为二进制文件 (读取前 1024 字节看是否有空字符)
    try:
        with open(file_path, 'rb') as f_check:
            chunk = f_check.read(1024)
            if b'\0' in chunk:
                return {"error": "检测到二进制内容，无法以文本方式读取"}
    except Exception:
        pass # 忽略检查错误，继续尝试读取

    try:
        content = []
        # errors='replace' 非常重要，防止日志里的乱码导致程序崩溃
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            if position == 'head':
                for _ in range(lines):
                    line = f.readline()
                    if not line: break
                    content.append(line.strip())
            else:
                # 对于小于 50MB 的文件，readlines 还是安全的
                all_lines = f.readlines()
                content = all_lines[-lines:] if len(all_lines) > lines else all_lines
                content = [line.strip() for line in content]

        return {
            "状态": "success",
            "文件路径": file_path,
            "读取模式": position,
            "行数": len(content),
            "content": "\n".join(content)
        }
    except PermissionError:
        return {"error": "无读取权限，请检查是否需要管理员/Root身份"}
    except Exception as e:
        return {"error": f"读取失败: {str(e)}"}

def find_large_files(directory: str = None, top_n: int = 5) -> list:
    """
    扫描指定目录下最大的 N 个文件。
    兼容：自动判断 Windows/Linux 默认路径
    """
    # 自动设置默认路径
    if directory is None:
        if platform.system() == "Windows":
            directory = os.getcwd() # Windows 默认扫当前目录，扫 C盘太慢
        else:
            directory = "/var/log"  # Linux 默认扫日志目录

    files_info = []

    try:
        # 遍历目录
        for root, dirs, files in os.walk(directory):
            for name in files:
                filepath = os.path.join(root, name)
                try:
                    # 使用 lstat 不跟踪软链接，防止死循环
                    size = os.path.getsize(filepath)
                    files_info.append((filepath, size))
                except (OSError, PermissionError):
                    continue
    except Exception as e:
        return [{"error": f"扫描出错: {str(e)}"}]

    # 排序并取 Top N
    files_info.sort(key=lambda x: x[1], reverse=True)
    
    result = []
    for path, size in files_info[:top_n]:
        result.append({
            "path": path,
            "size": _bytes_to_human(size),
            "size_bytes": size
        })
        
    return result

def list_directory(path: str = None, limit: int = 20) -> dict:
    """
    列出指定目录下的文件和子目录
    兼容：自动判断 Windows/Linux 默认路径
    """
    # 自动设置默认路径
    if path is None:
        if platform.system() == "Windows":
            path = os.getcwd() # Windows 默认当前目录
        else:
            path = "/var/log"  # Linux 默认日志目录

    if not os.path.exists(path):
        return {"error": f"目录不存在: {path}"}
    
    if not os.path.isdir(path):
        return {"error": f"这不是一个目录: {path}"}

    try:
        items = []
        with os.scandir(path) as it:
            count = 0
            for entry in it:
                if count >= limit:
                    break
                
                name = entry.name + ("/" if entry.is_dir() else "")
                
                size = "DIR"
                if entry.is_file():
                    try:
                        size = _bytes_to_human(entry.stat().st_size)
                    except:
                        size = "?"
                
                items.append(f"{name:<30} | {size}")
                count += 1
        
        return {
            "directory": path,
            "items": items,
            "total_count": count
        }
    except PermissionError:
        return {"error": f"无权访问目录: {path}"}
    except Exception as e:
        return {"error": str(e)}

def get_file_usage(user_message: str, base_dir: str) -> dict:
    """
    智能文件请求处理器：
    接收用户的自然语言，内部进行意图识别、路径提取、安全检查，
    最后调用相应的工具并返回结果。
    """
    user_cmd = user_message.lower()

    # 1. 定义关键词
    read_keywords = ["读取", "read", "内容", "cat", "显示"]
    info_keywords = ["属性", "详情", "大小", "权限", "info", "stat", "信息", "查看"]
    large_keywords = ["大文件", "large", "占用", "最大", "top"]
    search_keywords = ["找", "搜索", "search", "find", "查找"]

    # --- 辅助函数：提取文件名 ---
    def extract_path(text):
        # 1. 优先匹配引号内的内容
        quoted = re.search(r'["\'](.*?)["\']', text)
        if quoted:
                return quoted.group(1)
            
        pattern = r'(?:[a-zA-Z]:)?[\\/]?[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+'
            
        match = re.search(pattern, text)
        if match:
            return match.group(0)

        # 2. 尝试寻找像路径的单词
        words = text.split()
        cmd_keywords = read_keywords + info_keywords + large_keywords + search_keywords + ["文件", "名", "带有", "包含"]
            
        for w in words:
            # 过滤掉包含中文的词 (简单判断：如果长度大于1且全是ASCII字符)
            if w.isascii() and w.lower() not in cmd_keywords:
                return w.strip(".,;。，")
                
        return None
    
    # 提取文件名
    raw_filename = extract_path(user_message)
    target_file = None

    # 3. 安全检查与路径拼接
    if raw_filename:
        target_file, error = _resolve_target_path(raw_filename, base_dir)
        if error:
            return {"状态": "error", "信息": error}
        
    if any(k in user_cmd for k in search_keywords):
        clean_cmd = user_message
        for k in ["帮我", "找", "文件", "名", "带有", "包含", "搜索", "search", "find", "查找", "的"]:
            clean_cmd = clean_cmd.replace(k, " ")
        
        search_term = clean_cmd.strip()
        
        # 如果提取不到 (比如用户只输入了 "搜索"), 尝试用 extract_path 的结果
        if not search_term and raw_filename:
            search_term = raw_filename

        if search_term:
            # 默认在 base_dir 下搜索
            return search_files_by_name(base_dir, search_term)
        else:
            return {"状态": "error", "信息": "请指定要搜索的文件名关键词"}

    # A. 大文件/概览
    if any(k in user_cmd for k in large_keywords):
        return get_file_example_info(target_file or base_dir)

    # B. 属性
    if any(k in user_cmd for k in info_keywords) and target_file:
        return get_file_info(target_file)

    # C. 读取
    if any(k in user_cmd for k in read_keywords) and target_file:
        return read_file_content(target_file)

    # D. 默认列出目录
    return get_file_example_info(target_file or base_dir)
