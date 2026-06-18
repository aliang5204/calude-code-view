<template>
  <div class="chat-window">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="chat-header-left">
        <h3>{{ store.currentTitle }}</h3>
        <span v-if="store.currentConv?.group_tag" class="header-tag">
          {{ store.currentConv.group_tag }}
        </span>
      </div>
      <div class="chat-header-right">
        <span v-if="store.currentConv?.project_path" class="ctx-badge" :title="store.currentConv.project_path">
          📁 {{ basename(store.currentConv.project_path) }}
        </span>
        <span v-if="mountedFileCount > 0" class="ctx-badge">
          📄 {{ mountedFileCount }} 个文件
        </span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages-container" ref="msgContainer">
      <div v-if="store.messages.length === 0 && !store.isStreaming" class="empty-chat">
        <div class="empty-icon">✨</div>
        <p class="empty-title">开始对话</p>
        <p class="empty-hint">使用下方工具栏挂载项目目录或文件，让 AI 更好地理解你的上下文</p>
      </div>

      <MessageBubble
        v-for="msg in store.messages"
        :key="msg.id"
        :role="msg.role"
        :content="msg.content"
        :created-at="msg.created_at"
      />

      <!-- 流式输出 -->
      <div v-if="store.isStreaming && store.streamingContent" class="message-row assistant">
        <div class="msg-wrapper">
          <div class="msg-avatar"><span>🤖</span></div>
          <div class="msg-body">
            <div class="msg-header"><span class="msg-role">AI</span></div>
            <div class="msg-content streaming" v-html="renderedStreaming"></div>
          </div>
        </div>
      </div>

      <div v-if="store.isStreaming && !store.streamingContent" class="thinking-indicator">
        <span>AI 正在思考</span><span class="dot-anim">...</span>
      </div>

      <div v-if="store.error" class="error-bar">
        <span>❌ {{ store.error }}</span>
        <a-button type="link" size="small" @click="store.error = null">关闭</a-button>
      </div>
    </div>

    <!-- 输入区域 -->
    <div
      class="input-panel"
      :style="{ height: inputHeight + 'px' }"
    >
      <!-- 拖拽手柄 -->
      <div class="drag-handle" @mousedown="startResize">
        <div class="drag-bar" />
      </div>

      <!-- 已选择的文件标签 -->
      <div v-if="attachedFiles.length > 0" class="attached-files">
        <div
          v-for="(file, idx) in attachedFiles"
          :key="idx"
          class="file-chip"
          :title="file.path"
        >
          <span class="file-chip-icon">{{ fileIcon(file.path) }}</span>
          <span class="file-chip-name">{{ basename(file.path) }}</span>
          <span class="file-chip-remove" @click="removeFile(idx)">×</span>
        </div>
      </div>

      <!-- 文本输入 -->
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="chat-textarea"
        placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
        :disabled="store.isStreaming"
        @keydown="handleKeydown"
        @input="autoGrow"
      ></textarea>

      <!-- 底部工具栏 -->
      <div class="input-toolbar">
        <div class="toolbar-left">
          <a-tooltip title="挂载项目目录" placement="top">
            <button class="tool-btn" @click="pickDirectory" :disabled="store.isStreaming">
              <FolderOpenOutlined />
              <span>项目目录</span>
            </button>
          </a-tooltip>
          <a-tooltip title="挂载文件" placement="top">
            <button class="tool-btn" @click="pickFiles" :disabled="store.isStreaming">
              <FileTextOutlined />
              <span>选择文件</span>
            </button>
          </a-tooltip>
        </div>
        <div class="toolbar-right">
          <span class="char-count" v-if="inputText.length > 0">{{ inputText.length }}</span>
          <button
            class="send-btn"
            :disabled="!inputText.trim() || store.isStreaming"
            @click="handleSend()"
          >
            <span v-if="store.isStreaming">⏳</span>
            <span v-else>发送</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { FolderOpenOutlined, FileTextOutlined } from '@ant-design/icons-vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import { useChatStore } from '@/stores/chat'
import type { FileContext } from '@/api'
import MessageBubble from './MessageBubble.vue'

const store = useChatStore()
const inputText = ref('')
const msgContainer = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// 可拖拽的输入框高度
const inputHeight = ref(160)
const minInputHeight = 120
const maxInputHeight = 500
let isResizing = false

// 已挂载的文件
const attachedFiles = ref<FileContext[]>([])

const mountedFileCount = computed(() => {
  if (!store.currentConv?.file_paths) return 0
  try {
    const arr = JSON.parse(store.currentConv.file_paths)
    return Array.isArray(arr) ? arr.length : 0
  } catch { return 0 }
})

// ====== Markdown 流式渲染 ======
const renderedStreaming = computed(() => {
  marked.setOptions({
    highlight: (code: string, lang: string) => {
      if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value
      return hljs.highlightAuto(code).value
    },
    breaks: true,
  })
  return marked.parse(store.streamingContent) as string
})

function basename(p: string): string {
  return p.replace(/[/\\]$/, '').split(/[/\\]/).pop() || p
}

function fileIcon(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase()
  const map: Record<string, string> = {
    py: '🐍', js: '📜', ts: '📘', vue: '💚', html: '🌐', css: '🎨',
    json: '📋', md: '📝', txt: '📄', pdf: '📕', yaml: '⚙️', yml: '⚙️',
    go: '🔵', rs: '🦀', java: '☕', cpp: '⚡', c: '⚡', sh: '💻',
  }
  return map[ext || ''] || '📄'
}

// ====== 自动滚动 ======
function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

watch(() => store.messages.length, scrollToBottom)
watch(() => store.streamingContent, scrollToBottom)

// ====== 拖拽缩放输入框 ======
function startResize(e: MouseEvent) {
  isResizing = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

function onResize(e: MouseEvent) {
  if (!isResizing) return
  const chatEl = document.querySelector('.chat-window')
  if (!chatEl) return
  const rect = chatEl.getBoundingClientRect()
  const newHeight = rect.bottom - e.clientY
  inputHeight.value = Math.min(maxInputHeight, Math.max(minInputHeight, newHeight))
}

function stopResize() {
  isResizing = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})

// ====== 输入框自动增高 ======
function autoGrow() {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    const scrollH = el.scrollHeight
    const maxTextH = inputHeight.value - 60
    el.style.height = Math.min(scrollH, maxTextH) + 'px'
  })
}

// ====== 键盘处理 ======
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// ====== 发送消息 ======
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.isStreaming) return

  inputText.value = ''
  // 重置 textarea 高度
  nextTick(() => {
    if (textareaRef.value) textareaRef.value.style.height = 'auto'
  })

  const files = attachedFiles.value.length > 0 ? [...attachedFiles.value] : undefined
  attachedFiles.value = []
  await store.sendUserMessage(text, files)
}

// ====== 原生文件选择器 (File System Access API) ======
async function pickDirectory() {
  try {
    // @ts-ignore - File System Access API
    const dirHandle = await window.showDirectoryPicker()
    const files: FileContext[] = []
    await readDirRecursive(dirHandle, '', files)
    attachedFiles.value = [...attachedFiles.value, ...files]
  } catch (err: any) {
    if (err.name === 'AbortError') return // 用户取消
    // 降级：用传统 input
    fallbackDirPicker()
  }
}

async function readDirRecursive(
  dirHandle: any,
  prefix: string,
  results: FileContext[],
  depth = 0,
) {
  if (depth > 3) return
  const ignoreDirs = new Set([
    'node_modules', '.git', '.venv', 'venv', '__pycache__',
    'dist', 'build', '.next', '.nuxt', '.idea', '.vscode',
  ])

  for await (const [name, handle] of dirHandle.entries()) {
    if (handle.kind === 'directory') {
      if (!ignoreDirs.has(name) && !name.startsWith('.')) {
        await readDirRecursive(handle, prefix + name + '/', results, depth + 1)
      }
    } else {
      const ext = name.split('.').pop()?.toLowerCase()
      const textExts = new Set([
        'py', 'js', 'ts', 'jsx', 'tsx', 'vue', 'html', 'css', 'scss',
        'json', 'yaml', 'yml', 'xml', 'md', 'txt', 'sh', 'bat', 'ps1',
        'java', 'go', 'rs', 'cpp', 'c', 'h', 'hpp', 'cs', 'rb', 'php',
        'swift', 'kt', 'toml', 'ini', 'cfg', 'env', 'sql', 'graphql',
      ])
      if (!textExts.has(ext || '')) continue

      try {
        const fileHandle = await handle.getFile()
        const content = await fileHandle.text()
        if (content.length > 0 && content.length < 100000) {
          results.push({ path: prefix + name, content })
        }
      } catch { /* skip unreadable */ }
    }
  }
}

async function pickFiles() {
  try {
    // @ts-ignore - File System Access API
    const handles = await window.showOpenFilePicker({ multiple: true })
    const files: FileContext[] = []
    for (const handle of handles) {
      const file = await handle.getFile()
      const content = await file.text()
      if (content.length < 200000) {
        files.push({ path: handle.name, content })
      }
    }
    attachedFiles.value = [...attachedFiles.value, ...files]
  } catch (err: any) {
    if (err.name === 'AbortError') return
    fallbackFilePicker()
  }
}

// ====== 降级方案：传统 input 选择 ======
function fallbackDirPicker() {
  const input = document.createElement('input')
  input.type = 'file'
  // @ts-ignore
  input.webkitdirectory = true
  input.onchange = async () => {
    const fileList = input.files
    if (!fileList) return
    const files: FileContext[] = []
    for (let i = 0; i < Math.min(fileList.length, 50); i++) {
      const f = fileList[i]
      const ext = f.name.split('.').pop()?.toLowerCase()
      const textExts = new Set([
        'py', 'js', 'ts', 'jsx', 'tsx', 'vue', 'html', 'css', 'scss',
        'json', 'yaml', 'yml', 'xml', 'md', 'txt', 'sh', 'bat',
        'java', 'go', 'rs', 'cpp', 'c', 'h', 'hpp', 'toml', 'ini', 'sql',
      ])
      if (!textExts.has(ext || '')) continue
      try {
        const content = await f.text()
        if (content.length < 100000) {
          // webkitRelativePath 保留相对路径
          const relPath = (f as any).webkitRelativePath || f.name
          files.push({ path: relPath, content })
        }
      } catch { /* skip */ }
    }
    attachedFiles.value = [...attachedFiles.value, ...files]
  }
  input.click()
}

function fallbackFilePicker() {
  const input = document.createElement('input')
  input.type = 'file'
  input.multiple = true
  input.onchange = async () => {
    const fileList = input.files
    if (!fileList) return
    const files: FileContext[] = []
    for (let i = 0; i < fileList.length; i++) {
      const f = fileList[i]
      try {
        const content = await f.text()
        if (content.length < 200000) {
          files.push({ path: f.name, content })
        }
      } catch { /* skip */ }
    }
    attachedFiles.value = [...attachedFiles.value, ...files]
  }
  input.click()
}

// ====== 移除已选文件 ======
function removeFile(idx: number) {
  attachedFiles.value.splice(idx, 1)
}
</script>

<style scoped>
.chat-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0f0f1a;
  min-width: 0;
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  border-bottom: 1px solid #1e1e36;
  background: #12121f;
  min-height: 50px;
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-header-left h3 {
  font-size: 14px;
  font-weight: 600;
  color: #d0d0dc;
  margin: 0;
  max-width: 350px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-tag {
  font-size: 10px;
  background: #2a2a50;
  color: #8b8bf0;
  padding: 2px 8px;
  border-radius: 4px;
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ctx-badge {
  font-size: 11px;
  color: #6a6abb;
  background: #1a1a35;
  padding: 3px 8px;
  border-radius: 4px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border: 1px solid #252545;
}

/* Messages */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #4a4a68;
}

.empty-icon {
  font-size: 52px;
  margin-bottom: 12px;
}

.empty-title {
  font-size: 15px;
  color: #6a6a88;
  margin-bottom: 6px;
}

.empty-hint {
  font-size: 12px;
  color: #3e3e58;
  max-width: 320px;
  text-align: center;
  line-height: 1.5;
}

/* Streaming message */
.message-row.assistant {
  padding: 6px 0;
}

.msg-wrapper {
  display: flex;
  gap: 14px;
  max-width: 860px;
  margin: 0 auto;
  padding: 0 24px;
}

.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #1e1e36;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  border: 1px solid #2a2a45;
}

.msg-body { max-width: 78%; min-width: 0; }

.msg-header {
  margin-bottom: 4px;
  font-size: 11px;
  color: #5a5a78;
}

.msg-role {
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.msg-content {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.65;
  font-size: 14px;
  word-break: break-word;
  background: #1a1a30;
  color: #d0d0dc;
  border: 1px solid #252540;
  border-bottom-left-radius: 4px;
}

.msg-content.streaming {
  border-left: 2px solid #6c5ce7;
}

.msg-content :deep(pre) {
  background: #0d0d1a;
  border: 1px solid #252540;
  color: #d4d4d4;
  padding: 14px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.msg-content :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
}

.msg-content :deep(p) { margin: 4px 0; }
.msg-content :deep(p:first-child) { margin-top: 0; }
.msg-content :deep(p:last-child) { margin-bottom: 0; }

.thinking-indicator {
  padding: 16px 24px;
  color: #5a5a78;
  font-size: 14px;
  max-width: 860px;
  margin: 0 auto;
}

.dot-anim::after {
  content: '';
  animation: dots 1.5s steps(3, end) infinite;
}

@keyframes dots {
  0% { content: ''; }
  33% { content: '.'; }
  66% { content: '..'; }
  100% { content: '...'; }
}

.error-bar {
  background: #2d1520;
  color: #ff6b6b;
  padding: 10px 16px;
  margin: 8px 24px;
  border-radius: 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #3d1a2a;
  max-width: 860px;
  margin-left: auto;
  margin-right: auto;
}

/* Input Panel */
.input-panel {
  border-top: 1px solid #1e1e36;
  background: #12121f;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
}

.drag-handle {
  height: 8px;
  cursor: ns-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.drag-handle:hover .drag-bar {
  background: #6c5ce7;
}

.drag-bar {
  width: 40px;
  height: 3px;
  background: #2a2a45;
  border-radius: 2px;
  transition: background 0.2s;
}

/* Attached files */
.attached-files {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 8px 16px 0;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #1a1a35;
  border: 1px solid #2a2a50;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  color: #a0a0c0;
  max-width: 220px;
}

.file-chip-icon {
  font-size: 13px;
  flex-shrink: 0;
}

.file-chip-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-chip-remove {
  cursor: pointer;
  color: #6a6a88;
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
  flex-shrink: 0;
}

.file-chip-remove:hover {
  color: #ff6b6b;
}

/* Textarea */
.chat-textarea {
  flex: 1;
  width: 100%;
  border: none;
  background: transparent;
  color: #d0d0dc;
  font-size: 14px;
  line-height: 1.6;
  padding: 12px 16px 8px;
  resize: none;
  outline: none;
  font-family: inherit;
  min-height: 40px;
}

.chat-textarea::placeholder {
  color: #4a4a68;
}

.chat-textarea:disabled {
  opacity: 0.5;
}

/* Toolbar */
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px 10px;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  gap: 4px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: 1px solid #2a2a45;
  color: #8a8aa8;
  padding: 5px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
  transition: all 0.15s;
}

.tool-btn:hover {
  background: #1a1a35;
  color: #b0b0d0;
  border-color: #3a3a60;
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.char-count {
  font-size: 11px;
  color: #4a4a68;
}

.send-btn {
  background: linear-gradient(135deg, #6c5ce7, #5a4bd1);
  color: #fff;
  border: none;
  padding: 7px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
  min-width: 64px;
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #7d6ff0, #6a5ce0);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
}

.send-btn:disabled {
  background: #1e1e36;
  color: #4a4a68;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
