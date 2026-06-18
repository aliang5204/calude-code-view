import json
from typing import AsyncGenerator, List, Dict, Any, Optional
import httpx
from app.models import ApiConfig, Message


def mask_api_key(key: str) -> str:
    """脱敏 API Key，仅显示前4位和后4位"""
    if len(key) <= 8:
        return key[:2] + "****"
    return key[:4] + "****" + key[-4:]


async def estimate_chars(text: str) -> int:
    """估算文本字符数"""
    return len(text)


async def build_messages(
    conversation_messages: List[Message],
    user_content: str,
    project_path: str = "",
    file_paths_str: str = "[]",
    file_contexts: Optional[Dict[str, str]] = None,
    max_chars: int = 950_000,  # ~950KB，留 50KB 冗余
) -> List[Dict[str, Any]]:
    """
    组装发送给 LLM 的消息列表。
    优先级：system prompt → 项目上下文 → 文件上下文(前端直传) → 历史消息(从旧到新) → 当前用户消息
    """
    messages = []

    # ① System Prompt
    system_parts = [
        "You are a helpful AI assistant. You can understand and generate code, "
        "analyze files, and help with various tasks. Respond in the user's language."
    ]

    # ② 项目/文件上下文 — 后端挂载的目录和文件路径
    if project_path or (file_paths_str and file_paths_str != "[]"):
        try:
            file_paths = json.loads(file_paths_str) if file_paths_str else []
        except json.JSONDecodeError:
            file_paths = []

        context_parts = []
        if project_path:
            context_parts.append(f"### Project Directory: {project_path}")
            from app.services.context import scan_directory
            tree = scan_directory(project_path, max_depth=3)
            context_parts.append(f"File tree:\n{tree}")

        if file_paths:
            from app.services.context import read_file_content
            context_parts.append("### Mounted Files:")
            for fp in file_paths:
                content = read_file_content(fp)
                if content:
                    context_parts.append(f"\n#### {fp}\n```\n{content[:50000]}\n```")

        context_text = "\n".join(context_parts)
        if context_text:
            system_parts.append(f"\n## Project Context\n{context_text}")

    # ③ 前端直传的文件内容
    if file_contexts:
        fc_parts = ["### Attached Files:"]
        for fpath, fcontent in file_contexts.items():
            fc_parts.append(f"\n#### {fpath}\n```\n{fcontent[:50000]}\n```")
        system_parts.append("\n## Attached File Context\n" + "\n".join(fc_parts))

    system_text = "\n\n".join(system_parts)
    messages.append({"role": "system", "content": system_text})

    # ③ 历史消息 (从旧到新)，超出 950KB 则从最早截断
    current_size = len(system_text)
    history_messages = []
    for msg in conversation_messages:
        msg_size = len(msg.content) + 50  # role 等元数据开销估算
        if current_size + msg_size > max_chars:
            break  # 超出限制，截断更旧的消息
        history_messages.append({"role": msg.role, "content": msg.content})
        current_size += msg_size

    messages.extend(history_messages)

    # ④ 当前用户消息已在 conversation_messages 末尾，不需要重复添加
    # 但如果历史消息为空（新会话），需要手动添加用户消息
    if not history_messages:
        messages.append({"role": "user", "content": user_content})

    return messages


async def stream_llm_response(
    config: ApiConfig,
    messages: List[Dict[str, Any]],
) -> AsyncGenerator[str, None]:
    """
    流式调用大模型 API，逐 chunk yield。
    兼容 OpenAI API 格式 (DeepSeek 等已兼容)。
    """
    url = config.base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": config.default_model,
        "messages": messages,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
