<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  mapUrl: string | null
  isLoading: boolean
}>()

const iframeLoaded = ref(false)

watch(() => props.mapUrl, () => {
  iframeLoaded.value = false
})

function onIframeLoad() {
  iframeLoaded.value = true
}
</script>

<template>
  <div class="map-viewer">
    <!-- Initial state -->
    <div v-if="!mapUrl && !isLoading" class="placeholder">
      <div class="placeholder-content">
        <div class="placeholder-icon">🚇</div>
        <h2>Metro Voronoi Map</h2>
        <p>Select a city and click "Generate Map" to visualize metro station coverage areas.</p>
        <p class="explanation">
          Each colored region represents the area closest to a particular metro station,
          calculated using <strong>Voronoi diagrams</strong>.
        </p>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="spinner"></div>
        <p>Generating Voronoi diagram...</p>
        <p class="loading-hint">This may take a minute for new cities</p>
      </div>
    </div>

    <!-- Map iframe -->
    <iframe
      v-if="mapUrl"
      :src="mapUrl"
      class="map-iframe"
      :class="{ loaded: iframeLoaded }"
      @load="onIframeLoad"
    ></iframe>
  </div>
</template>

<style scoped>
.map-viewer {
  flex: 1;
  position: relative;
  background: #2a2a2a;
  overflow: hidden;
}

.placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3a3a3a 0%, #2a2a2a 100%);
}

.placeholder-content {
  text-align: center;
  color: #aaa;
  max-width: 500px;
  padding: 40px;
}

.placeholder-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.7;
}

.placeholder-content h2 {
  font-family: 'Georgia', serif;
  font-size: 28px;
  font-weight: normal;
  color: #ccc;
  margin: 0 0 15px 0;
}

.placeholder-content p {
  font-size: 14px;
  line-height: 1.6;
  margin: 10px 0;
}

.explanation {
  font-size: 12px !important;
  color: #888;
  font-style: italic;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 30, 30, 0.95);
  z-index: 10;
}

.loading-content {
  text-align: center;
  color: #ccc;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #444;
  border-top-color: #888;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-content p {
  font-family: 'Georgia', serif;
  font-size: 16px;
  margin: 5px 0;
}

.loading-hint {
  font-size: 12px !important;
  color: #777;
  font-style: italic;
}

.map-iframe {
  width: 100%;
  height: 100%;
  border: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.map-iframe.loaded {
  opacity: 1;
}
</style>

