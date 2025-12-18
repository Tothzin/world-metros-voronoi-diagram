// API Service for Metro Voronoi
import type {
  PopularCitiesResponse,
  GenerateMapResponse,
  HealthResponse
} from '@/types/api'

const API_BASE = '/api'

export async function getPopularCities(): Promise<PopularCitiesResponse> {
  const response = await fetch(`${API_BASE}/popular-cities`)
  if (!response.ok) {
    throw new Error('Failed to fetch popular cities')
  }
  return response.json()
}

export async function generateMap(
  city: string,
  forceRegenerate: boolean = false
): Promise<GenerateMapResponse> {
  const response = await fetch(`${API_BASE}/generate-map`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      city,
      force_regenerate: forceRegenerate
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to generate map')
  }

  return response.json()
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error('API not available')
  }
  return response.json()
}

export function getMapUrl(slug: string): string {
  return `${API_BASE}/map/${slug}`
}

