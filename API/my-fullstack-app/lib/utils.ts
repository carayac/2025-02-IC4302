import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export interface CourseFilters {
  search?: string
  category?: string
  estimatedWeeks?: number
  language?: string
  currency?: string
  studentsRange?: string 
  entityType?: string
  entityValue?: string
  sortBy?: 'rating_value' | 'price' | 'students' | 'title'
  order?: 'asc' | 'desc'
  limit?: number
  page?: number
}

export interface PaginatedResponse<T> {
  success: boolean
  data: T
  pagination: {
    currentPage: number
    totalPages: number
    totalCount: number
    limit: number
    hasNextPage: boolean
    hasPrevPage: boolean
  }
  facets?: {
    categories?: Array<{ name: string; count: number }>
    estimatedWeeks?: Array<{ name: string; count: number }> 
    languages?: Array<{ name: string; count: number }>
    currencies?: Array<{ name: string; count: number }>
    priceRange?: {
      minPrice: number
      maxPrice: number
      avgPrice: number
      buckets: Array<{ range: number; count: number }>
    }
    ratingDistribution?: Array<{ _id: number; count: number }>
    studentsRange?: {
      buckets: Array<{ range: number; count: number }>
    }
    entityTypes?: Array<{ name: string; count: number }>
    entityValues?: Array<{ name: string; count: number }>
  }
  filters?: CourseFilters
  error?: string
  message?: string
}

export interface CourseResponse {
  success: boolean
  data: any
  error?: string
  message?: string
}

// Helper para obtener la URL base
function getBaseUrl() {
  if (typeof window !== 'undefined') {
    return ''
  }
  if (process.env.NEXT_PUBLIC_BASE_URL) {
    return process.env.NEXT_PUBLIC_BASE_URL
  }
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`
  }
  return `http://localhost:${process.env.PORT ?? 3000}`
}

export async function fetchCourses(
  filters: CourseFilters = {}
): Promise<PaginatedResponse<any[]>> {
  const params = new URLSearchParams()

  if (filters.search) params.append('search', filters.search)
  if (filters.category) params.append('category', filters.category)
  if (filters.estimatedWeeks) params.append('estimatedWeeks', filters.estimatedWeeks.toString())  
  if (filters.language) params.append('language', filters.language)
  if (filters.currency) params.append('currency', filters.currency)
  if (filters.studentsRange) params.append('studentsRange', filters.studentsRange)
  if (filters.entityType) params.append('entityType', filters.entityType)
  if (filters.entityValue) params.append('entityValue', filters.entityValue)
  if (filters.sortBy) params.append('sortBy', filters.sortBy)
  if (filters.order) params.append('order', filters.order)
  if (filters.limit) params.append('limit', filters.limit.toString())
  if (filters.page) params.append('page', filters.page.toString())

  const baseUrl = getBaseUrl()
  const url = `${baseUrl}/api/courses?${params.toString()}`

  const response = await fetch(url, {
    cache: 'no-store',
    credentials: 'include',
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.message || 'Error al cargar cursos')
  }

  return response.json()
}

export async function fetchCourse(id: string, search?: string, token?: string): Promise<CourseResponse> {
  const params = new URLSearchParams()
  if (search) params.append('search', search)

  const baseUrl = getBaseUrl()
  const queryString = params.toString()
  const url = `${baseUrl}/api/courses/${id}${queryString ? `?${queryString}` : ''}`

  console.log('Fetching course from:', url)

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }

  // Si hay token, inclúyelo como Cookie header
  if (token) {
    headers['Cookie'] = `auth-token=${token}`
  }

  const response = await fetch(url, {
    cache: 'no-store',
    credentials: 'include',
    headers,
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Curso no encontrado')
    }
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.message || 'Error al cargar el curso')
  }

  return response.json()
}

export function formatPrice(price: number, currency: string = 'USD'): string {
  if (price === 0) return 'Gratis'
  
  const currencySymbols: Record<string, string> = {
    USD: '$',
    EUR: '€',
    GBP: '£',
    INR: '₹',
    BRL: 'R$',
  }

  const symbol = currencySymbols[currency] || currency
  return `${symbol}${price.toFixed(2)}`
}

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