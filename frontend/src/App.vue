<template>
  <a-config-provider :theme="themeConfig">
    <div id="app-container">
      <router-view />
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { theme } from 'ant-design-vue'
import { ref } from 'vue'

const { darkAlgorithm, defaultAlgorithm } = theme

const themeConfig = ref({
  algorithm: darkAlgorithm,
  token: {
    colorPrimary: '#6c5ce7',
    colorBgBase: '#0f0f1a',
    colorBgContainer: '#1a1a2e',
    colorBgElevated: '#1e1e36',
    colorBorder: '#2a2a45',
    colorText: '#e0e0e8',
    colorTextSecondary: '#a0a0b8',
    borderRadius: 8,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
  },
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app, #app-container {
  height: 100%;
  width: 100%;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #0f0f1a;
  color: #e0e0e8;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #3a3a55;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #4a4a65;
}

/* Selection */
::selection {
  background: #6c5ce720;
  color: #c4b5fd;
}
</style>
