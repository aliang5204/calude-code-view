<template>
  <div class="chat-layout">
    <div class="sidebar-panel" :style="{ width: sidebarWidth + 'px' }">
      <Sidebar />
    </div>
    <div
      class="sidebar-resize-handle"
      @mousedown="startSidebarResize"
    >
      <div class="resize-line" />
    </div>
    <div class="chat-panel">
      <ChatWindow />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import ChatWindow from '@/components/ChatWindow.vue'

const sidebarWidth = ref(280)
const minSidebar = 200
const maxSidebar = 480
let resizing = false

function startSidebarResize(e: MouseEvent) {
  resizing = true
  document.addEventListener('mousemove', onSidebarResize)
  document.addEventListener('mouseup', stopSidebarResize)
  e.preventDefault()
}

function onSidebarResize(e: MouseEvent) {
  if (!resizing) return
  const w = Math.min(maxSidebar, Math.max(minSidebar, e.clientX))
  sidebarWidth.value = w
}

function stopSidebarResize() {
  resizing = false
  document.removeEventListener('mousemove', onSidebarResize)
  document.removeEventListener('mouseup', stopSidebarResize)
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onSidebarResize)
  document.removeEventListener('mouseup', stopSidebarResize)
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100%;
  width: 100%;
}

.sidebar-panel {
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-resize-handle {
  width: 5px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: transparent;
  transition: background 0.2s;
  z-index: 10;
}

.sidebar-resize-handle:hover,
.sidebar-resize-handle:active {
  background: #1e1e36;
}

.resize-line {
  width: 1px;
  height: 40px;
  background: #2a2a45;
  border-radius: 1px;
  transition: background 0.2s;
}

.sidebar-resize-handle:hover .resize-line {
  background: #6c5ce7;
}

.chat-panel {
  flex: 1;
  min-width: 0;
}
</style>
