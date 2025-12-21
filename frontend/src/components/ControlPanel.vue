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
const isMenuOpen = ref(false)

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

onMounted(async () => {
  try {
    const response = await getPopularCities()
    cities.value = response.cities
    if (cities.value.length > 0 && cities.value[0]) {
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
  <!-- Hamburger button (mobile only) -->
  <button class="hamburger-btn" @click="toggleMenu" :class="{ open: isMenuOpen }">
    <span></span>
    <span></span>
    <span></span>
  </button>

  <!-- Overlay (mobile only) -->
  <div class="overlay" v-if="isMenuOpen" @click="toggleMenu"></div>

  <div class="control-panel" :class="{ open: isMenuOpen }">
    <div class="panel-header">
      <h1>METRONOID</h1>
      <p class="subtitle">Voronoi Coverage Diagrams</p>
      <button class="close-btn" @click="toggleMenu">✕</button>
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
/* Hamburger button (mobile only) */
.hamburger-btn {
  display: none;
  position: fixed;
  top: 50%;
  left: 10px;
  transform: translateY(-50%);
  z-index: 1001;
  width: 38px;
  height: 38px;
  background: linear-gradient(to bottom, #4a4a4a, #333);
  border: 2px outset #666;
  border-radius: 4px;
  cursor: pointer;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  padding: 0;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.4);
}

.hamburger-btn span {
  display: block;
  width: 22px;
  height: 2.5px;
  background: #f0f0f0;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.hamburger-btn:hover {
  background: linear-gradient(to bottom, #5a5a5a, #444);
}

.hamburger-btn:active {
  border-style: inset;
}

/* Hide hamburger when menu is open (we have X button in header) */
.hamburger-btn.open {
  display: none;
}

/* Overlay (mobile only) */
.overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.control-panel {
  width: 320px;
  background: linear-gradient(to bottom, #f5f5f0, #e8e8e0);
  border-right: 3px solid #999;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  font-family: 'Georgia', 'Times New Roman', serif;
  overflow-y: auto;
  transition: transform 0.3s ease;
}

.panel-header {
  background: linear-gradient(to bottom, #4a4a4a, #333);
  color: #f0f0f0;
  padding: 20px 15px;
  text-align: center;
  border-bottom: 3px solid #222;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
  position: relative;
}

.close-btn {
  display: none;
  position: absolute;
  top: 10px;
  right: 10px;
  background: transparent;
  border: none;
  color: #f0f0f0;
  font-size: 28px;
  cursor: pointer;
  width: 35px;
  height: 35px;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
  transition: opacity 0.2s;
  z-index: 1;
}

.close-btn:hover {
  opacity: 1;
  transform: scale(1.1);
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

/* Mobile styles */
@media (max-width: 768px) {
  .hamburger-btn {
    display: flex;
  }

  .overlay {
    display: block;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
  }

  .overlay {
    opacity: 1;
    pointer-events: auto;
  }

  .control-panel {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 1000;
    transform: translateX(-100%);
    box-shadow: 4px 0 12px rgba(0, 0, 0, 0.5);
  }

  .control-panel.open {
    transform: translateX(0);
  }

  .close-btn {
    display: block;
  }
}
</style>

