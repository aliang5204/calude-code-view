import json
import os
import shutil
import asyncio
from typing import AsyncGenerator, Dict, Any


def _find_claude() -> str:
    """查找 Claude Code CLI"""
    if env_bin := os.environ.get("CLAUDE_BIN"):
        return env_bin

    candidates = [
        "E:/code/develop/nvm-setup/nodejs/node_modules/@anthropic-ai/claude-code/bin/claude.exe",
        os.path.expanduser("~/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"),
    ]
    for p in candidates:
        p = os.path.expanduser(p)
        if os.path.exists(p):
            return p

    resolved = shutil.which("claude")
    return resolved if resolved else "claude"


async def stream_claude_response(
    prompt: str,
    session_id: str = "",
) -> AsyncGenerator[Dict[str, Any], None]:
    """调用 Claude Code CLI，流式返回 JSON 事件。"""

    claude_bin = _find_claude()

    args = [
        claude_bin,
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
    ]
    if session_id:
        args.extend(["--resume", session_id])

    # 默认在项目根目录工作
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    cwd = project_root if os.path.isdir(project_root) else None
    env = os.environ.copy()

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
    except Exception as e:
        import traceback
        err_detail = f"Failed to start Claude: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        yield {"type": "error", "error": err_detail}
        return

    try:
        async for line in proc.stdout:
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                continue
            try:
                event = json.loads(line_str)
                yield event
            except json.JSONDecodeError:
                continue

        await proc.wait()

        if proc.returncode != 0:
            try:
                stderr_bytes = await proc.stderr.read()
                stderr_text = stderr_bytes.decode("utf-8", errors="replace")[:500]
            except Exception:
                stderr_text = ""
            if stderr_text.strip():
                yield {"type": "error", "error": f"Claude({proc.returncode}): {stderr_text}"}

    except Exception as e:
        yield {"type": "error", "error": f"Stream error: {type(e).__name__}: {e}"}


def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return key[:2] + "****"
    return key[:4] + "****" + key[-4:]
