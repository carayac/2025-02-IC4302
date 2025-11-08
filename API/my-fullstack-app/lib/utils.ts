import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export interface CourseFilters {
  search?: string
  category?: string
  specificCategory?: string
  language?: string
  currency?: string
  minRating?: number
  minPrice?: number
  maxPrice?: number
  minStudents?: number
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
    specificCategories?: Array<{ name: string; count: number }>
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

export async function fetchCourses(
  filters: CourseFilters = {}
): Promise<PaginatedResponse<any[]>> {
  const params = new URLSearchParams()

  if (filters.search) params.append('search', filters.search)
  if (filters.category) params.append('category', filters.category)
  if (filters.specificCategory) params.append('specificCategory', filters.specificCategory)
  if (filters.language) params.append('language', filters.language)
  if (filters.currency) params.append('currency', filters.currency)
  if (filters.minRating) params.append('minRating', filters.minRating.toString())
  if (filters.minPrice) params.append('minPrice', filters.minPrice.toString())
  if (filters.maxPrice) params.append('maxPrice', filters.maxPrice.toString())
  if (filters.minStudents) params.append('minStudents', filters.minStudents.toString())
  if (filters.sortBy) params.append('sortBy', filters.sortBy)
  if (filters.order) params.append('order', filters.order)
  if (filters.limit) params.append('limit', filters.limit.toString())
  if (filters.page) params.append('page', filters.page.toString())

  const response = await fetch(`/api/courses?${params.toString()}`, {
    cache: 'no-store',
  })

  if (!response.ok) {
    throw new Error('Error al cargar cursos')
  }

  return response.json()
}

export async function fetchCourse(id: string, search?: string): Promise<CourseResponse> {
  const params = new URLSearchParams()
  if (search) params.append('search', search)

  const response = await fetch(`/api/courses/${id}?${params.toString()}`, {
    cache: 'no-store',
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Curso no encontrado')
    }
    throw new Error('Error al cargar el curso')
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