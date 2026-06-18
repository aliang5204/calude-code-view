import { defineStore } from 'pinia'
import { ref } from 'vue'
import { configApi, type ApiConfig } from '@/api'

export const useSettingsStore = defineStore('settings', () => {
  const configs = ref<ApiConfig[]>([])
  const loading = ref(false)

  async function loadConfigs() {
    loading.value = true
    try {
      configs.value = await configApi.list()
    } finally {
      loading.value = false
    }
  }

  async function createConfig(data: Partial<ApiConfig>) {
    const cfg = await configApi.create(data)
    await loadConfigs()
    return cfg
  }

  async function updateConfig(id: number, data: Partial<ApiConfig>) {
    const cfg = await configApi.update(id, data)
    await loadConfigs()
    return cfg
  }

  async function deleteConfig(id: number) {
    await configApi.delete(id)
    await loadConfigs()
  }

  return { configs, loading, loadConfigs, createConfig, updateConfig, deleteConfig }
})
