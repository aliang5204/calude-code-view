<template>
  <div class="chat-layout">
    <Sidebar @open-settings="showSettings = true" />
    <ChatWindow />
    <SettingsModal v-model:open="showSettings" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'
import SettingsModal from '@/components/SettingsModal.vue'

const showSettings = ref(false)
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  width: 100%;
}
</style>
