<template>
  <div class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-icon">🤖</span>
      <span class="brand-text">AI Chat</span>
    </div>

    <div class="sidebar-header">
      <a-button type="primary" block size="large" @click="handleNewChat">
        <template #icon><PlusOutlined /></template>
        新建对话
      </a-button>
    </div>

    <div class="sidebar-filter">
      <a-select
        v-model:value="selectedTag"
        style="width: 100%"
        placeholder="筛选标签"
        @change="handleTagChange"
        allowClear
        size="small"
        :options="tagOptions"
      />
    </div>

    <div class="sidebar-list">
      <a-spin v-if="loading" class="loading-spin" />
      <div v-else-if="store.conversations.length === 0" class="empty-hint">
        <div class="empty-icon">💬</div>
        <p>暂无对话</p>
        <p class="empty-sub">点击上方按钮开始</p>
      </div>
      <div
        v-for="conv in store.conversations"
        :key="conv.id"
        :class="['conv-item', { active: conv.id === store.currentConvId }]"
        @click="handleSelect(conv)"
      >
        <div class="conv-item-main">
          <div class="conv-title">{{ conv.title || '新对话' }}</div>
          <div class="conv-preview">{{ conv.first_message || '暂无消息' }}</div>
          <div class="conv-meta">
            <span v-if="conv.group_tag" class="conv-tag">{{ conv.group_tag }}</span>
            <span class="conv-time">{{ formatTime(conv.updated_at) }}</span>
          </div>
        </div>
        <a-dropdown trigger="click" placement="bottomRight">
          <a-button type="text" size="small" class="conv-more-btn" @click.stop>
            <MoreOutlined />
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item @click.stop="showTagModal(conv)">
                <EditOutlined /> 设置标签
              </a-menu-item>
              <a-menu-item danger @click.stop="handleDelete(conv.id)">
                <DeleteOutlined /> 删除对话
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="footer-info">Claude Code + ccswitch</div>
    </div>

    <!-- 标签编辑弹窗 -->
    <a-modal
      v-model:open="tagModalVisible"
      title="设置对话标签"
      @ok="handleTagSave"
      @cancel="tagModalVisible = false"
      width="360px"
    >
      <a-input v-model:value="editingTag" placeholder="输入标签名称" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { PlusOutlined, MoreOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { useChatStore } from '@/stores/chat'
import type { ConversationListItem } from '@/api'

const store = useChatStore()
const selectedTag = ref<string | undefined>(undefined)
const tagModalVisible = ref(false)
const editingTag = ref('')
const editingConvId = ref<number | null>(null)
const loading = ref(false)

const tagOptions = computed(() => [
  { value: '', label: '全部对话' },
  ...Array.from(new Set(store.conversations.map(c => c.group_tag).filter(Boolean)))
    .sort()
    .map(tag => ({ value: tag, label: tag })),
])

function formatTime(dateStr?: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function handleNewChat() {
  loading.value = true
  try { await store.createConversation() } finally { loading.value = false }
}

async function handleSelect(conv: ConversationListItem) {
  loading.value = true
  try { await store.selectConversation(conv.id) } finally { loading.value = false }
}

async function handleDelete(id: number) {
  await store.deleteConversation(id)
}

function handleTagChange(value: string) {
  store.setActiveTag(value || '')
  store.loadConversations(value || undefined)
}

function showTagModal(conv: ConversationListItem) {
  editingConvId.value = conv.id
  editingTag.value = conv.group_tag
  tagModalVisible.value = true
}

async function handleTagSave() {
  if (editingConvId.value !== null) {
    await store.updateConversation({ group_tag: editingTag.value })
  }
  tagModalVisible.value = false
}

onMounted(() => store.loadConversations())
</script>

<style scoped>
.sidebar {
  height: 100%;
  background: #12121f;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 8px;
}

.brand-icon {
  font-size: 24px;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #e0e0e8;
  letter-spacing: -0.5px;
}

.sidebar-header {
  padding: 8px 12px 4px;
}

.sidebar-filter {
  padding: 8px 12px;
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.loading-spin {
  display: flex;
  justify-content: center;
  padding: 32px;
}

.empty-hint {
  text-align: center;
  color: #5a5a78;
  padding: 40px 16px;
  font-size: 13px;
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 12px;
  color: #3e3e58;
  margin-top: 4px;
}

.conv-item {
  display: flex;
  align-items: flex-start;
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 2px;
  transition: all 0.15s;
  color: #a0a0b8;
}

.conv-item:hover {
  background: #1a1a30;
  color: #c0c0d0;
}

.conv-item.active {
  background: #1e1e38;
  color: #e0e0e8;
  box-shadow: inset 2px 0 0 #6c5ce7;
}

.conv-item-main {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.conv-preview {
  font-size: 11px;
  color: #5a5a78;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 4px;
}

.conv-tag {
  font-size: 10px;
  background: #2a2a50;
  color: #8b8bf0;
  padding: 1px 6px;
  border-radius: 3px;
}

.conv-time {
  font-size: 10px;
  color: #4a4a68;
}

.conv-more-btn {
  opacity: 0;
  transition: opacity 0.15s;
  color: #6a6a88 !important;
}

.conv-item:hover .conv-more-btn {
  opacity: 1;
}

.sidebar-footer {
  padding: 8px 12px;
  border-top: 1px solid #1e1e36;
}

.footer-info {
  font-size: 10px;
  color: #4a4a68;
  text-align: center;
}
</style>
