'use client'

import { useState, useEffect } from 'react'
import { Search, Filter, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { fetchCourses, formatPrice, formatStudents, type CourseFilters } from '@/lib/utils'
import Link from 'next/link'

interface CourseSearchProps {
  initialCategories: string[]
  initialLanguages: string[]
}

export function CourseSearch({ initialCategories, initialLanguages }: CourseSearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState<CourseFilters>({
    limit: 20,
    page: 1,
  })
  const [courses, setCourses] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState<any>(null)

  // Cargar cursos cuando cambian los filtros
  useEffect(() => {
    loadCourses()
  }, [filters])

  const loadCourses = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetchCourses(filters)
      setCourses(response.data)
      setPagination(response.pagination)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar cursos')
      console.error('Error loading courses:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setFilters(prev => ({ ...prev, search: searchQuery, page: 1 }))
  }

  const handleFilterChange = (key: keyof CourseFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }))
  }

  const clearFilters = () => {
    setSearchQuery('')
    setFilters({ limit: 20, page: 1 })
  }

  const handlePageChange = (newPage: number) => {
    setFilters(prev => ({ ...prev, page: newPage }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="space-y-6">
      {/* Barra de búsqueda */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Buscar cursos por título, descripción o categoría..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? 'Buscando...' : 'Buscar'}
            </Button>
            
            {/* Filtros avanzados */}
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon">
                  <Filter className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>Filtros Avanzados</SheetTitle>
                  <SheetDescription>
                    Refina tu búsqueda con filtros adicionales
                  </SheetDescription>
                </SheetHeader>
                <div className="space-y-4 py-4">
                  {/* Categoría */}
                  <div className="space-y-2">
                    <Label>Categoría</Label>
                    <Select
                      value={filters.category || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('category', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todas las categorías" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas las categorías</SelectItem>
                        {initialCategories.map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {cat}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Idioma */}
                  <div className="space-y-2">
                    <Label>Idioma</Label>
                    <Select
                      value={filters.language || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('language', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todos los idiomas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos los idiomas</SelectItem>
                        {initialLanguages.map((lang) => (
                          <SelectItem key={lang} value={lang}>
                            {lang}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Rating mínimo */}
                  <div className="space-y-2">
                    <Label>Rating Mínimo</Label>
                    <Select
                      value={filters.minRating?.toString() || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('minRating', value === 'all' ? undefined : parseFloat(value))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Cualquier rating" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Cualquier rating</SelectItem>
                        <SelectItem value="4.5">4.5+ ⭐</SelectItem>
                        <SelectItem value="4.0">4.0+ ⭐</SelectItem>
                        <SelectItem value="3.5">3.5+ ⭐</SelectItem>
                        <SelectItem value="3.0">3.0+ ⭐</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Ordenar por */}
                  <div className="space-y-2">
                    <Label>Ordenar por</Label>
                    <Select
                      value={filters.sortBy || 'rating_value'}
                      onValueChange={(value: any) => handleFilterChange('sortBy', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="rating_value">Rating</SelectItem>
                        <SelectItem value="students">Estudiantes</SelectItem>
                        <SelectItem value="price">Precio</SelectItem>
                        <SelectItem value="title">Título</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Orden */}
                  <div className="space-y-2">
                    <Label>Orden</Label>
                    <Select
                      value={filters.order || 'desc'}
                      onValueChange={(value: any) => handleFilterChange('order', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="desc">Mayor a menor</SelectItem>
                        <SelectItem value="asc">Menor a mayor</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button onClick={clearFilters} variant="outline" className="w-full">
                    <X className="mr-2 h-4 w-4" />
                    Limpiar Filtros
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
          </form>
        </CardContent>
      </Card>

      {/* Filtros activos */}
      {(filters.search || filters.category || filters.language || filters.minRating) && (
        <div className="flex flex-wrap gap-2">
          {filters.search && (
            <Badge variant="secondary">
              Búsqueda: {filters.search}
              <X
                className="ml-1 h-3 w-3 cursor-pointer"
                onClick={() => handleFilterChange('search', undefined)}
              />
            </Badge>
          )}
          {filters.category && (
            <Badge variant="secondary">
              Categoría: {filters.category}
              <X
                className="ml-1 h-3 w-3 cursor-pointer"
                onClick={() => handleFilterChange('category', undefined)}
              />
            </Badge>
          )}
          {filters.language && (
            <Badge variant="secondary">
              Idioma: {filters.language}
              <X
                className="ml-1 h-3 w-3 cursor-pointer"
                onClick={() => handleFilterChange('language', undefined)}
              />
            </Badge>
          )}
          {filters.minRating && (
            <Badge variant="secondary">
              Rating: {filters.minRating}+ ⭐
              <X
                className="ml-1 h-3 w-3 cursor-pointer"
                onClick={() => handleFilterChange('minRating', undefined)}
              />
            </Badge>
          )}
        </div>
      )}

      {/* Resultados */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="space-y-2">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-3 bg-muted rounded" />
                  <div className="h-3 bg-muted rounded w-5/6" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : courses.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground">
              No se encontraron cursos con los filtros seleccionados.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              Mostrando {courses.length} de {pagination?.totalCount || 0} cursos
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {courses.map((course) => (
              <Link key={course._id} href={`/courses/${course._id}`}>
                <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <img
                      src={course.image || '/placeholder-course.jpg'}
                      alt={course.title}
                      className="w-full h-40 object-cover rounded-md mb-2"
                    />
                    <CardTitle className="line-clamp-2">{course.title}</CardTitle>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {course['short-description']}
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>⭐ {course.rating_value.toFixed(1)}</span>
                      <span className="text-muted-foreground">
                        👥 {formatStudents(course.students)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary">{course.general_category}</Badge>
                      <span className="font-bold">
                        {formatPrice(course.price, course.currency)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      🌐 {course.language}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {/* Paginación */}
          {pagination && pagination.totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                disabled={!pagination.hasPrevPage || loading}
                onClick={() => handlePageChange(pagination.currentPage - 1)}
              >
                Anterior
              </Button>
              <span className="flex items-center px-4">
                Página {pagination.currentPage} de {pagination.totalPages}
              </span>
              <Button
                variant="outline"
                disabled={!pagination.hasNextPage || loading}
                onClick={() => handlePageChange(pagination.currentPage + 1)}
              >
                Siguiente
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}