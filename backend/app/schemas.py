from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== API Config ==========

class ApiConfigCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    default_model: str
    is_active: bool = False


class ApiConfigUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    is_active: Optional[bool] = None


class ApiConfigOut(BaseModel):
    id: int
    name: str
    base_url: str
    api_key: str  # 返回脱敏后的 key，前端仅用于展示
    default_model: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ========== Conversation ==========

class ConversationCreate(BaseModel):
    title: str = ""
    group_tag: str = ""
    model_config_id: Optional[int] = None
    project_path: str = ""
    file_paths: str = "[]"


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    group_tag: Optional[str] = None
    project_path: Optional[str] = None
    file_paths: Optional[str] = None


class ConversationOut(BaseModel):
    id: int
    title: str
    group_tag: str
    model_config_id: Optional[int] = None
    project_path: str
    file_paths: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConversationListItem(BaseModel):
    id: int
    title: str
    group_tag: str
    first_message: Optional[str] = None
    message_count: int = 0
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ========== Message ==========

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ========== Chat ==========

class FileContext(BaseModel):
    path: str
    content: str


class ChatSendRequest(BaseModel):
    content: str
    file_contexts: Optional[List[FileContext]] = None


# ========== Context ==========

class ReadFilesRequest(BaseModel):
    paths: List[str]


class ScanDirRequest(BaseModel):
    path: str
    max_depth: int = 3
