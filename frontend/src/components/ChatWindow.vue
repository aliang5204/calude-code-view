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
    </div>

    <!-- 消息列表 -->
    <div class="messages-container" ref="msgContainer">
      <div v-if="store.messages.length === 0 && !store.isStreaming" class="empty-chat">
        <div class="empty-icon">✨</div>
        <p class="empty-title">开始对话</p>
        <p class="empty-hint">点击右上角 📁 图标挂载项目目录，Claude Code 将在该目录下工作</p>
      </div>

      <MessageBubble
        v-for="msg in store.messages"
        :key="msg.id"
        :role="msg.role"
        :content="msg.content"
        :created-at="msg.created_at"
      />

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
    <div class="input-panel" :style="{ height: inputHeight + 'px' }">
      <div class="drag-handle" @mousedown="startResize">
        <div class="drag-bar" />
      </div>

      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="chat-textarea"
        placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
        :disabled="store.isStreaming"
        @keydown="handleKeydown"
        @input="autoGrow"
      ></textarea>

      <div class="input-toolbar">
        <div class="toolbar-left" />
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
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import { useChatStore } from '@/stores/chat'
import MessageBubble from './MessageBubble.vue'

const store = useChatStore()
const inputText = ref('')
const msgContainer = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const inputHeight = ref(160)
const minInputHeight = 120
const maxInputHeight = 500
let isResizing = false

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

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

watch(() => store.messages.length, scrollToBottom)
watch(() => store.streamingContent, scrollToBottom)

// ====== 输入框拖拽 ======
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
  inputHeight.value = Math.min(maxInputHeight, Math.max(minInputHeight, rect.bottom - e.clientY))
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

function autoGrow() {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    const maxTextH = inputHeight.value - 60
    el.style.height = Math.min(el.scrollHeight, maxTextH) + 'px'
  })
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.isStreaming) return
  inputText.value = ''
  nextTick(() => { if (textareaRef.value) textareaRef.value.style.height = 'auto' })
  await store.sendUserMessage(text)
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

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-bottom: 1px solid #1e1e36;
  background: #12121f;
  min-height: 44px;
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-header-left h3 {
  font-size: 14px; font-weight: 600; color: #d0d0dc; margin: 0;
  max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.header-tag {
  font-size: 10px; background: #2a2a50; color: #8b8bf0;
  padding: 2px 8px; border-radius: 4px;
}

.messages-container {
  flex: 1; overflow-y: auto; padding: 8px 0;
}

.empty-chat {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; color: #4a4a68;
}

.empty-icon { font-size: 52px; margin-bottom: 12px; }
.empty-title { font-size: 15px; color: #6a6a88; margin-bottom: 6px; }
.empty-hint { font-size: 12px; color: #3e3e58; max-width: 300px; text-align: center; line-height: 1.5; }

.message-row.assistant { padding: 5px 0; }

.msg-wrapper {
  display: flex; gap: 10px; max-width: 100%; margin: 0; padding: 0 10px;
}

.msg-avatar {
  width: 30px; height: 30px; border-radius: 6px; background: #1e1e36;
  display: flex; align-items: center; justify-content: center; font-size: 14px;
  flex-shrink: 0; border: 1px solid #2a2a45;
}

.msg-body { max-width: 82%; min-width: 0; }

.msg-header { margin-bottom: 4px; font-size: 11px; color: #5a5a78; }

.msg-role {
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}

.msg-content {
  padding: 12px 16px; border-radius: 12px; line-height: 1.65; font-size: 14px;
  word-break: break-word; background: #1a1a30; color: #d0d0dc;
  border: 1px solid #252540; border-bottom-left-radius: 4px;
}

.msg-content.streaming { border-left: 2px solid #6c5ce7; }

.msg-content :deep(pre) {
  background: #0d0d1a; border: 1px solid #252540; color: #d4d4d4;
  padding: 14px 16px; border-radius: 8px; overflow-x: auto; margin: 8px 0;
}

.msg-content :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; font-size: 13px;
}

.msg-content :deep(p) { margin: 4px 0; }

.thinking-indicator {
  padding: 10px 14px; color: #5a5a78; font-size: 14px;
}

.dot-anim::after {
  content: ''; animation: dots 1.5s steps(3, end) infinite;
}

@keyframes dots {
  0% { content: ''; } 33% { content: '.'; } 66% { content: '..'; } 100% { content: '...'; }
}

.error-bar {
  background: #2d1520; color: #ff6b6b; padding: 10px 16px; margin: 8px 14px;
  border-radius: 8px; font-size: 13px; display: flex; align-items: center;
  justify-content: space-between; border: 1px solid #3d1a2a;
}

.input-panel {
  border-top: 1px solid #1e1e36; background: #12121f;
  display: flex; flex-direction: column; flex-shrink: 0; position: relative;
}

.drag-handle {
  height: 8px; cursor: ns-resize; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0;
}

.drag-handle:hover .drag-bar { background: #6c5ce7; }

.drag-bar {
  width: 40px; height: 3px; background: #2a2a45; border-radius: 2px; transition: background 0.2s;
}

.chat-textarea {
  flex: 1; width: 100%; border: none; background: transparent; color: #d0d0dc;
  font-size: 14px; line-height: 1.6; padding: 10px 14px 6px; resize: none;
  outline: none; font-family: inherit; min-height: 40px;
}

.chat-textarea::placeholder { color: #4a4a68; }
.chat-textarea:disabled { opacity: 0.5; }

.input-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 10px 8px; flex-shrink: 0;
}

.toolbar-left { display: flex; gap: 6px; align-items: center; flex: 1; min-width: 0; overflow: hidden; }
.toolbar-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.tool-btn {
  display: flex; align-items: center; gap: 5px;
  background: transparent; border: 1px solid #2a2a45; color: #8a8aa8;
  padding: 5px 10px; border-radius: 6px; cursor: pointer;
  font-size: 12px; font-family: inherit; transition: all 0.15s; flex-shrink: 0;
}

.tool-btn:hover { background: #1a1a35; color: #b0b0d0; border-color: #3a3a60; }
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.mounted-path {
  font-size: 11px; color: #8b8bf0; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; max-width: 420px; flex-shrink: 1;
}

.mounted-remove {
  cursor: pointer; color: #5a5a78; font-size: 14px; padding: 0 2px; margin-left: 2px;
}

.mounted-remove:hover { color: #ff6b6b; }

.char-count { font-size: 11px; color: #4a4a68; }

.send-btn {
  background: linear-gradient(135deg, #6c5ce7, #5a4bd1); color: #fff;
  border: none; padding: 7px 20px; border-radius: 8px; font-size: 13px;
  font-weight: 600; cursor: pointer; font-family: inherit; transition: all 0.15s; min-width: 64px;
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #7d6ff0, #6a5ce0);
  transform: translateY(-1px); box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
}

.send-btn:disabled { background: #1e1e36; color: #4a4a68; cursor: not-allowed; }
</style>
