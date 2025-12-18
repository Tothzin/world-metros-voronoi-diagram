// API Types for Metro Voronoi

export interface City {
  name: string
  slug: string
}

export interface PopularCitiesResponse {
  cities: City[]
}

export interface GenerateMapRequest {
  city: string
  force_regenerate?: boolean
}

export interface GenerateMapResponse {
  success: boolean
  city: string
  slug: string
  map_url: string
  cached: boolean
}

export interface HealthResponse {
  status: string
  cached_maps: number
}

export interface ErrorResponse {
  detail: string
}

