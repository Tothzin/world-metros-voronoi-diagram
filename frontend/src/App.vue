<script setup lang="ts">
import { ref } from 'vue'
import ControlPanel from './components/ControlPanel.vue'
import MapViewer from './components/MapViewer.vue'

const mapUrl = ref<string | null>(null)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

function handleMapLoaded(url: string) {
  mapUrl.value = url
  errorMessage.value = null
}

function handleLoading(loading: boolean) {
  isLoading.value = loading
  if (loading) {
    errorMessage.value = null
  }
}

function handleError(message: string) {
  errorMessage.value = message
}
</script>

<template>
  <div class="app-container">
    <ControlPanel
      @map-loaded="handleMapLoaded"
      @loading="handleLoading"
      @error="handleError"
    />
    <MapViewer :map-url="mapUrl" :is-loading="isLoading" />

    <!-- Error toast -->
    <Transition name="fade">
      <div v-if="errorMessage" class="error-toast" @click="errorMessage = null">
        <span class="error-icon">⚠️</span>
        {{ errorMessage }}
        <span class="close-hint">(click to dismiss)</span>
      </div>
    </Transition>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

body {
  font-family: 'Georgia', 'Times New Roman', serif;
}
</style>

<style scoped>
.app-container {
  display: flex;
  height: 100%;
  width: 100%;
}

.error-toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(to bottom, #8b0000, #5a0000);
  color: #fff;
  padding: 12px 20px;
  border: 2px solid #400;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  font-size: 14px;
  cursor: pointer;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-icon {
  font-size: 18px;
}

.close-hint {
  font-size: 11px;
  opacity: 0.7;
  font-style: italic;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
