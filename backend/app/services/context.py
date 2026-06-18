import os
from typing import List

IGNORE_DIRS = {
    "node_modules", ".venv", "venv", ".git", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt",
    "target", ".mvn", ".gradle", "egg-info", ".tox", ".eggs",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
}

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".xml", ".md", ".txt", ".sh", ".bat", ".ps1",
    ".env", ".gitignore", ".dockerignore", ".cfg", ".ini", ".toml",
    ".java", ".go", ".rs", ".cpp", ".c", ".h", ".hpp", ".cs", ".rb",
    ".php", ".swift", ".kt", ".scala", ".r", ".sql", ".graphql",
    ".conf", ".proto", ".mk", ".cmake",
}


def is_text_file(filepath: str) -> bool:
    """判断文件是否为文本文件（非二进制）"""
    _, ext = os.path.splitext(filepath)
    return ext.lower() in TEXT_EXTENSIONS


def scan_directory(root_path: str, max_depth: int = 3) -> str:
    """扫描目录结构，返回格式化的文件树字符串"""
    root_path = os.path.abspath(root_path)
    lines = []

    def walk(path: str, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except PermissionError:
            lines.append(f"{prefix}[Permission Denied]")
            return

        # 分离目录和文件，过滤忽略目录
        dirs = []
        files_list = []
        for e in entries:
            full = os.path.join(path, e)
            if os.path.isdir(full):
                if e not in IGNORE_DIRS and not e.startswith("."):
                    dirs.append(e)
            elif os.path.isfile(full):
                if is_text_file(full):
                    files_list.append(e)

        all_items = dirs + files_list
        for i, item in enumerate(dirs):
            is_last = (i == len(all_items) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item}/")
            extension = "    " if is_last else "│   "
            walk(os.path.join(path, item), prefix + extension, depth + 1)

        for i, item in enumerate(files_list):
            idx = len(dirs) + i
            is_last = (idx == len(all_items) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item}")

    root_name = os.path.basename(root_path) or root_path
    lines.append(f"{root_name}/")
    walk(root_path, "", 0)
    return "\n".join(lines)


def read_file_content(filepath: str, max_chars: int = 50000) -> str:
    """读取文件内容，超出限制则截断"""
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        return f"[Error: File not found: {filepath}]"
    if not is_text_file(filepath):
        return f"[Skipped: Binary file: {filepath}]"
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
            truncated = f.read(1)  # 检查是否还有更多内容
            if truncated:
                content += "\n... [truncated]"
            return content
    except Exception as e:
        return f"[Error reading file: {e}]"


def read_files_content(paths: List[str]) -> dict:
    """批量读取文件内容"""
    results = {}
    for p in paths:
        results[p] = read_file_content(p)
    return results
