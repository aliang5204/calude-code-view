<template>
  <div :class="['message-row', role]">
    <div class="msg-wrapper">
      <div class="msg-avatar">
        <span v-if="role === 'user'">👤</span>
        <span v-else>🤖</span>
      </div>
      <div class="msg-body">
        <div class="msg-header">
          <span class="msg-role">{{ role === 'user' ? 'You' : 'AI' }}</span>
          <span class="msg-time">{{ formattedTime }}</span>
        </div>
        <div class="msg-content" v-html="renderedContent"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

const props = defineProps<{
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt?: string
}>()

const formattedTime = computed(() => {
  if (!props.createdAt) return ''
  const d = new Date(props.createdAt)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const renderedContent = computed(() => {
  if (props.role === 'user') {
    return escapeHtml(props.content).replace(/\n/g, '<br/>')
  }
  marked.setOptions({
    highlight: (code: string, lang: string) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value
      }
      return hljs.highlightAuto(code).value
    },
    breaks: true,
  })
  return marked.parse(props.content) as string
})

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
</script>

<style scoped>
.message-row {
  padding: 6px 0;
}

.msg-wrapper {
  display: flex;
  gap: 14px;
  max-width: 860px;
  margin: 0 auto;
  padding: 0 24px;
}

.message-row.user .msg-wrapper {
  flex-direction: row-reverse;
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

.message-row.user .msg-avatar {
  background: #2d2d60;
  border-color: #3d3d80;
}

.msg-body {
  max-width: 78%;
  min-width: 0;
}

.message-row.user .msg-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.msg-header {
  display: flex;
  gap: 8px;
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
}

.message-row.user .msg-content {
  background: linear-gradient(135deg, #6c5ce7, #5a4bd1);
  color: #f0f0f8;
  border-bottom-right-radius: 4px;
}

.message-row.assistant .msg-content {
  background: #1a1a30;
  color: #d0d0dc;
  border: 1px solid #252540;
  border-bottom-left-radius: 4px;
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

.msg-content :deep(p) {
  margin: 4px 0;
}

.msg-content :deep(p:first-child) {
  margin-top: 0;
}

.msg-content :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-content :deep(ul), .msg-content :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.msg-content :deep(li) {
  margin: 2px 0;
}

.msg-content :deep(blockquote) {
  border-left: 3px solid #6c5ce7;
  padding-left: 12px;
  margin: 8px 0;
  color: #8888a8;
}

.msg-content :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
  font-size: 13px;
}

.msg-content :deep(th), .msg-content :deep(td) {
  border: 1px solid #2a2a45;
  padding: 8px 12px;
  text-align: left;
}

.msg-content :deep(th) {
  background: #1e1e36;
  font-weight: 600;
}

.msg-content :deep(a) {
  color: #8b8bf0;
}

.msg-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}

.msg-content :deep(hr) {
  border: none;
  border-top: 1px solid #2a2a45;
  margin: 12px 0;
}
</style>
