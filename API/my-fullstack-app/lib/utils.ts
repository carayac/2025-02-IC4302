import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Obtener la URL base de la API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'

// Tipos para las respuestas de la API
export interface CourseFilters {
  search?: string
  category?: string
  language?: string
  minRating?: number
  minPrice?: number
  maxPrice?: number
  sortBy?: 'rating_value' | 'price' | 'students' | 'title'
  order?: 'asc' | 'desc'
  limit?: number
  page?: number
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> extends ApiResponse<T> {
  pagination: {
    currentPage: number
    totalPages: number
    totalCount: number
    limit: number
    hasNextPage: boolean
    hasPrevPage: boolean
  }
  filters: CourseFilters
}

/**
 * Obtener todos los cursos con filtros opcionales
 */
export async function fetchCourses(
  filters: CourseFilters = {}
): Promise<PaginatedResponse<any[]>> {
  const params = new URLSearchParams()

  // Agregar parámetros al query string
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, value.toString())
    }
  })

  const url = `${API_URL}/api/courses${params.toString() ? `?${params}` : ''}`

  const response = await fetch(url, {
    cache: 'no-store',
    next: { revalidate: 0 },
  })

  if (!response.ok) {
    throw new Error(`Error al obtener cursos: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Obtener un curso específico por ID
 */
export async function fetchCourse(id: string): Promise<ApiResponse<any>> {
  const response = await fetch(`${API_URL}/api/courses/${id}`, {
    cache: 'force-cache',
    next: { revalidate: 60 },
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Curso no encontrado')
    }
    throw new Error(`Error al obtener curso: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Formatear precio con símbolo de moneda
 */
export function formatPrice(price: number, currency: string = 'USD'): string {
  if (price === 0) return 'Gratis'
  
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: currency,
  }).format(price)
}

/**
 * Formatear número de estudiantes (ej: 1500 → 1.5K)
 */
export function formatStudents(students: number): string {
  if (students >= 1000000) {
    return `${(students / 1000000).toFixed(1)}M`
  }
  if (students >= 1000) {
    return `${(students / 1000).toFixed(1)}K`
  }
  return students.toString()
}

/**
 * Formatear rating con estrellas
 */
export function formatRating(rating: number): string {
  const fullStars = Math.floor(rating)
  const hasHalfStar = rating % 1 >= 0.5
  return `${'⭐'.repeat(fullStars)}${hasHalfStar ? '⭐' : ''} (${rating.toFixed(1)})`
}