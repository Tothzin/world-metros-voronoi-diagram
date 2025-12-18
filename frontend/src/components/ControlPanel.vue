<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { City } from '@/types/api'
import { getPopularCities, generateMap, getMapUrl } from '@/services/api'

const emit = defineEmits<{
  mapLoaded: [url: string]
  loading: [isLoading: boolean]
  error: [message: string]
}>()

const cities = ref<City[]>([])
const selectedCity = ref('')
const customCity = ref('')
const forceRegenerate = ref(false)
const isLoading = ref(false)
const statusMessage = ref('')

onMounted(async () => {
  try {
    const response = await getPopularCities()
    cities.value = response.cities
    if (cities.value.length > 0) {
      selectedCity.value = cities.value[0].name
    }
  } catch (e) {
    emit('error', 'Could not load cities list')
  }
})

async function handleGenerate() {
  const city = customCity.value.trim() || selectedCity.value
  if (!city) {
    emit('error', 'Please select or enter a city')
    return
  }

  isLoading.value = true
  emit('loading', true)
  statusMessage.value = 'Downloading station data from OpenStreetMap...'

  try {
    const response = await generateMap(city, forceRegenerate.value)
    statusMessage.value = response.cached ? 'Loaded from cache!' : 'Map generated successfully!'
    emit('mapLoaded', getMapUrl(response.slug))
  } catch (e: any) {
    statusMessage.value = ''
    emit('error', e.message || 'Error generating map')
  } finally {
    isLoading.value = false
    emit('loading', false)
  }
}
</script>

<template>
  <div class="control-panel">
    <div class="panel-header">
      <h1>METROMAP</h1>
      <p class="subtitle">Voronoi Coverage Diagrams</p>
    </div>

    <div class="panel-section">
      <label class="section-label">1. Select a city from the list:</label>
      <select v-model="selectedCity" :disabled="isLoading" class="city-select">
        <option v-for="city in cities" :key="city.slug" :value="city.name">
          {{ city.name }}
        </option>
      </select>
    </div>

    <div class="panel-section">
      <label class="section-label">Or type a custom city name:</label>
      <input
        v-model="customCity"
        type="text"
        placeholder="e.g., Berlin, Germany"
        :disabled="isLoading"
        class="city-input"
        @keyup.enter="handleGenerate"
      />
      <p class="hint">Use format: "City, Country"</p>
    </div>

    <div class="panel-section">
      <label class="checkbox-label">
        <input type="checkbox" v-model="forceRegenerate" :disabled="isLoading" />
        Force regenerate (ignore cache)
      </label>
    </div>

    <div class="panel-section">
      <button @click="handleGenerate" :disabled="isLoading" class="generate-btn">
        {{ isLoading ? 'Generating...' : 'Generate Map' }}
      </button>
    </div>

    <div v-if="statusMessage" class="status-message">
      {{ statusMessage }}
    </div>

    <div class="panel-footer">
      <p>Data from <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a></p>
      <p class="version">v1.0</p>
    </div>
  </div>
</template>

<style scoped>
.control-panel {
  width: 320px;
  background: linear-gradient(to bottom, #f5f5f0, #e8e8e0);
  border-right: 3px solid #999;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  font-family: 'Georgia', 'Times New Roman', serif;
  overflow-y: auto;
}

.panel-header {
  background: linear-gradient(to bottom, #4a4a4a, #333);
  color: #f0f0f0;
  padding: 20px 15px;
  text-align: center;
  border-bottom: 3px solid #222;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.panel-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: normal;
  letter-spacing: 3px;
}

.subtitle {
  margin: 5px 0 0 0;
  font-size: 12px;
  color: #bbb;
  font-style: italic;
}

.panel-section {
  padding: 15px;
  border-bottom: 1px solid #ccc;
}

.section-label {
  display: block;
  font-size: 13px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.city-select, .city-input {
  width: 100%;
  padding: 8px 10px;
  font-size: 14px;
  font-family: 'Georgia', serif;
  border: 2px inset #ccc;
  background: #fff;
  box-sizing: border-box;
}

.city-select:focus, .city-input:focus {
  outline: none;
  border-color: #666;
  background: #fffef5;
}

.hint {
  font-size: 11px;
  color: #777;
  margin: 5px 0 0 0;
  font-style: italic;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #444;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.generate-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  font-family: 'Georgia', serif;
  font-weight: bold;
  background: linear-gradient(to bottom, #5a5a5a, #333);
  color: #fff;
  border: 2px outset #666;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.generate-btn:hover:not(:disabled) {
  background: linear-gradient(to bottom, #6a6a6a, #444);
}

.generate-btn:active:not(:disabled) {
  border-style: inset;
}

.generate-btn:disabled {
  background: #999;
  cursor: not-allowed;
}

.status-message {
  padding: 10px 15px;
  background: #fffde7;
  border-bottom: 1px solid #ccc;
  font-size: 12px;
  color: #555;
  font-style: italic;
}

.panel-footer {
  margin-top: auto;
  padding: 15px;
  background: #ddd;
  border-top: 2px solid #bbb;
  font-size: 11px;
  color: #666;
  text-align: center;
}

.panel-footer a {
  color: #444;
}

.version {
  margin: 5px 0 0 0;
  font-size: 10px;
  color: #999;
}
</style>

