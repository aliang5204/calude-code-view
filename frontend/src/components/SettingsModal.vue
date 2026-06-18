<template>
  <a-modal
    v-model:open="visible"
    title="模型与 API 管理"
    :footer="null"
    width="560px"
    :body-style="{ padding: '0', maxHeight: '70vh', overflow: 'auto' }"
    @cancel="handleClose"
    destroyOnClose
  >
    <div class="settings-modal">
      <div class="modal-toolbar">
        <a-button type="primary" size="small" @click="showAddModal">
          <template #icon><PlusOutlined /></template>
          新增配置
        </a-button>
      </div>

      <a-spin :spinning="store.loading">
        <div v-if="store.configs.length === 0 && !store.loading" class="empty-state">
          <span class="empty-icon">🔧</span>
          <p>还没有 API 配置</p>
          <p class="empty-sub">添加大模型 API 配置即可开始使用</p>
        </div>

        <div v-else class="config-list">
          <div v-for="item in store.configs" :key="item.id" class="config-item">
            <div class="config-main">
              <div class="config-name">
                {{ item.name }}
                <span v-if="item.is_active" class="active-badge">当前使用</span>
              </div>
              <div class="config-details">
                <div class="detail-row">
                  <span class="detail-label">Base URL</span>
                  <span class="detail-value">{{ item.base_url }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">API Key</span>
                  <span class="detail-value mono">{{ item.api_key }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">模型</span>
                  <span class="detail-value mono">{{ item.default_model }}</span>
                </div>
              </div>
            </div>
            <div class="config-actions">
              <a-button type="text" size="small" @click="showEditModal(item)">编辑</a-button>
              <a-popconfirm title="确定删除？" @confirm="handleDelete(item.id)">
                <a-button type="text" size="small" danger>删除</a-button>
              </a-popconfirm>
            </div>
          </div>
        </div>
      </a-spin>
    </div>

    <!-- 新增/编辑弹窗（嵌套在 settings 弹窗内） -->
    <a-modal
      v-model:open="formVisible"
      :title="editingId ? '编辑配置' : '新增配置'"
      @ok="handleSave"
      @cancel="formVisible = false"
      :confirm-loading="saving"
      width="420px"
    >
      <a-form layout="vertical" style="margin-top: 8px;">
        <a-form-item label="配置名称">
          <a-input v-model:value="form.name" placeholder="DeepSeek / OpenAI" />
        </a-form-item>
        <a-form-item label="Base URL">
          <a-input v-model:value="form.base_url" placeholder="https://api.deepseek.com/v1" />
        </a-form-item>
        <a-form-item label="API Key">
          <a-input-password v-model:value="form.api_key" placeholder="sk-..." />
        </a-form-item>
        <a-form-item label="默认模型">
          <a-input v-model:value="form.default_model" placeholder="deepseek-chat" />
        </a-form-item>
        <a-form-item>
          <a-switch v-model:checked="form.is_active" />
          <span style="margin-left: 8px; font-size: 12px; color: #888;">设为默认使用</span>
        </a-form-item>
      </a-form>
    </a-modal>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useSettingsStore } from '@/stores/settings'
import type { ApiConfig } from '@/api'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [value: boolean] }>()

const store = useSettingsStore()
const visible = ref(false)
const formVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = reactive({
  name: '', base_url: '', api_key: '', default_model: '', is_active: false,
})

watch(() => props.open, (val) => {
  visible.value = val
  if (val) store.loadConfigs()
})

function handleClose() {
  emit('update:open', false)
}

function resetForm() {
  form.name = ''; form.base_url = ''; form.api_key = ''
  form.default_model = ''; form.is_active = false
  editingId.value = null
}

function showAddModal() { resetForm(); formVisible.value = true }
function showEditModal(item: ApiConfig) {
  editingId.value = item.id
  form.name = item.name; form.base_url = item.base_url; form.api_key = ''
  form.default_model = item.default_model; form.is_active = item.is_active
  formVisible.value = true
}

async function handleSave() {
  if (!form.name || !form.base_url || !form.default_model) { message.warning('请填写必要字段'); return }
  if (!editingId.value && !form.api_key) { message.warning('请填写 API Key'); return }
  saving.value = true
  try {
    const data: any = { name: form.name, base_url: form.base_url, default_model: form.default_model, is_active: form.is_active }
    if (form.api_key) data.api_key = form.api_key
    if (editingId.value) { await store.updateConfig(editingId.value, data); message.success('已更新') }
    else { await store.createConfig(data); message.success('已创建') }
    formVisible.value = false
  } catch (e: any) { message.error(e.message || '操作失败') }
  finally { saving.value = false }
}

async function handleDelete(id: number) {
  try { await store.deleteConfig(id); message.success('已删除') }
  catch (e: any) { message.error(e.message) }
}
</script>

<style scoped>
.settings-modal { padding: 0; }

.modal-toolbar {
  display: flex; justify-content: flex-end;
  padding: 12px 16px; border-bottom: 1px solid #1e1e36;
}

.empty-state {
  text-align: center; padding: 48px 16px; color: #5a5a78;
}

.empty-icon { font-size: 36px; display: block; margin-bottom: 12px; }
.empty-sub { font-size: 12px; color: #3e3e58; margin-top: 4px; }

.config-list { max-height: 380px; overflow-y: auto; }

.config-item {
  display: flex; align-items: flex-start; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid #1a1a30;
  transition: background 0.15s;
}

.config-item:last-child { border-bottom: none; }
.config-item:hover { background: #16162a; }

.config-name {
  font-size: 13px; font-weight: 600; color: #d0d0dc;
  display: flex; align-items: center; gap: 8px;
}

.active-badge {
  font-size: 10px; background: #1a3a2a; color: #4ade80;
  padding: 1px 8px; border-radius: 10px;
}

.config-details { margin-top: 4px; }

.detail-row {
  display: flex; gap: 8px; font-size: 11px; margin-top: 1px;
}

.detail-label { color: #5a5a78; min-width: 55px; flex-shrink: 0; }
.detail-value { color: #8a8aa8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-value.mono { font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 10px; }

.config-actions {
  display: flex; gap: 2px; flex-shrink: 0; margin-left: 8px;
}
</style>
