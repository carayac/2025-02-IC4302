'use client'

import { HighlightedText } from '@/components/ui/highlighted-text'
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

interface RangeItem {
  value: number
  label: string
  count: number
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
  const [facets, setFacets] = useState<any>(null)

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
      setFacets(response.facets)
      console.log('Facets recibidos:', response.facets)
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



  // Obtener rangos de estudiantes con conteos
  const getStudentsRanges = (): RangeItem[] => {
    if (!facets?.studentsRange?.buckets) return []
    
    const studentsLabels: { [key: number]: string } = {
      0: '0 - 100',
      100: '100 - 500',
      500: '500 - 1K',
      1000: '1K - 5K',
      5000: '5K - 10K',
      10000: '10K - 50K',
      50000: '50K - 100K',
      100000: '100K - 1M'
    }
    
    return facets.studentsRange.buckets
      .filter((bucket: any) => typeof bucket.range === 'number')
      .map((bucket: any) => ({
        value: bucket.range,
        label: studentsLabels[bucket.range] || `${bucket.range}+`,
        count: bucket.count
      }))
      .sort((a: any, b: any) => a.value - b.value)
  }

  const getNextRange = (current: number) => {
    const ranges = [0, 100, 500, 1000, 5000, 10000, 50000, 100000, 1000000]
    const currentIndex = ranges.indexOf(current)
    if (currentIndex === -1 || currentIndex === ranges.length - 1) return '1000000'
    return ranges[currentIndex + 1].toString()
  }

  const studentsRanges = getStudentsRanges()
  const totalStudents = studentsRanges.reduce((sum: number, s: RangeItem) => sum + s.count, 0)
  const totalEstimatedWeeks = (facets?.estimatedWeeks || []).reduce((sum: number, w: any) => sum + w.count, 0)
  
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
                placeholder="Buscar cursos por título, descripción..."
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
                  <SheetTitle>Facets de Búsqueda</SheetTitle>
                  <SheetDescription>
                    Filtra por categoría, idioma, moneda, rating, estudiantes y entidades
                  </SheetDescription>
                </SheetHeader>
                <div className="space-y-6 py-4 overflow-y-auto max-h-[calc(100vh-120px)]">
                  
                  {/* Facet 1: Categoría General (stringFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">📚 Categoría General</Label>
                    <Select
                      value={filters.category || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('category', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todas las categorías" />
                      </SelectTrigger>
                      <SelectContent className="max-h-[300px]">
                        <SelectItem value="all">
                          Todas las categorías
                          {facets?.categories && ` (${facets.categories.reduce((sum: number, c: any) => sum + c.count, 0)})`}
                        </SelectItem>
                        {(facets?.categories || initialCategories.map(c => ({ name: c, count: 0 }))).map((cat: any) => (
                          <SelectItem key={cat.name} value={cat.name}>
                            {cat.name} 
                            {cat.count > 0 && <span className="text-muted-foreground ml-1">({cat.count})</span>}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Facet 2: Categoría Específica (stringFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">⏱️ Semanas Estimadas</Label>
                    <Select
                        value={filters.estimatedWeeks?.toString() || 'all'}                      onValueChange={(value) =>
                        handleFilterChange('estimatedWeeks', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todas las subcategorías" />
                      </SelectTrigger>
                      <SelectContent className="max-h-[300px]">
                        <SelectItem value="all">
                          Todas las duraciones
                          {totalEstimatedWeeks > 0 && ` (${totalEstimatedWeeks})`}
                        </SelectItem>
                        {(facets?.estimatedWeeks || []).map((weeks: any) => (
                          <SelectItem key={weeks.name} value={weeks.name.toString()}>
                            {weeks.name} {weeks.name === 1 ? 'semana' : 'semanas'}
                            {weeks.count > 0 && <span className="text-muted-foreground ml-1">({weeks.count})</span>}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Facet 3: Idioma (stringFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">🌐 Idioma</Label>
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
                        <SelectItem value="all">
                          Todos los idiomas
                          {facets?.languages && ` (${facets.languages.reduce((sum: number, l: any) => sum + l.count, 0)})`}
                        </SelectItem>
                        {(facets?.languages || initialLanguages.map(l => ({ name: l, count: 0 }))).map((lang: any) => (
                          <SelectItem key={lang.name} value={lang.name}>
                            {lang.name}
                            {lang.count > 0 && <span className="text-muted-foreground ml-1">({lang.count})</span>}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Facet 4: Moneda (stringFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">💱 Moneda</Label>
                    <Select
                      value={filters.currency || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('currency', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todas las monedas" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">
                          Todas las monedas
                          {facets?.currencies && ` (${facets.currencies.reduce((sum: number, c: any) => sum + c.count, 0)})`}
                        </SelectItem>
                        {(facets?.currencies || []).map((curr: any) => (
                          <SelectItem key={curr.name} value={curr.name}>
                            {curr.name}
                            {curr.count > 0 && <span className="text-muted-foreground ml-1">({curr.count})</span>}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>


                  {/* Facet 6: Número de Estudiantes (numberFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">👥 Rango de Estudiantes</Label>
                    <Select
                      value={filters.studentsRange || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('studentsRange', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todos los cursos" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">
                          Todos los cursos
                          {totalStudents > 0 && ` (${totalStudents})`}
                        </SelectItem>
                        {studentsRanges.length > 0 ? (
                          studentsRanges.map((range) => (
                            <SelectItem key={range.value} value={`${range.value}-${getNextRange(range.value)}`}>
                              {range.label}
                              <span className="text-muted-foreground ml-1">({range.count})</span>
                            </SelectItem>
                          ))
                        ) : (
                          <>
                            <SelectItem value="0-100">0 - 100</SelectItem>
                            <SelectItem value="100-500">100 - 500</SelectItem>
                            <SelectItem value="500-1000">500 - 1K</SelectItem>
                            <SelectItem value="1000-5000">1K - 5K</SelectItem>
                            <SelectItem value="5000-10000">5K - 10K</SelectItem>
                            <SelectItem value="10000-50000">10K - 50K</SelectItem>
                            <SelectItem value="50000-100000">50K - 100K</SelectItem>
                            <SelectItem value="100000-1000000">100K - 1M</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Facet 7: Entity Type (stringFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">🏷️ Tipo de Entidad</Label>
                    <Select
                      value={filters.entityType || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('entityType', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todos los tipos" />
                      </SelectTrigger>
                      <SelectContent className="max-h-[300px]">
                        <SelectItem value="all">
                          Todos los tipos
                          {facets?.entityTypes && ` (${facets.entityTypes.reduce((sum: number, e: any) => sum + e.count, 0)})`}
                        </SelectItem>
                        {(facets?.entityTypes || []).map((entity: any) => (
                          <SelectItem key={entity.name} value={entity.name}>
                            {entity.name}
                            {entity.count > 0 && <span className="text-muted-foreground ml-1">({entity.count})</span>}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* NUEVO Facet 8: Entity Value (stringFacet) */}
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">🔖 Valor de Entidad</Label>
                    <Select
                      value={filters.entityValue || 'all'}
                      onValueChange={(value) =>
                        handleFilterChange('entityValue', value === 'all' ? undefined : value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Todos los valores" />
                      </SelectTrigger>
                      <SelectContent className="max-h-[300px]">
                        <SelectItem value="all">
                          Todos los valores
                          {facets?.entityValues && ` (${facets.entityValues.reduce((sum: number, e: any) => sum + e.count, 0)})`}
                        </SelectItem>
                        {(facets?.entityValues || []).map((entity: any) => (
                          <SelectItem key={entity.name} value={entity.name}>
                            {entity.name}
                            {entity.count > 0 && <span className="text-muted-foreground ml-1">({entity.count})</span>}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Botón limpiar filtros */}
                  <Button onClick={clearFilters} variant="outline" className="w-full mt-4">
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
      {(filters.search || filters.category || filters.estimatedWeeks || filters.language || filters.currency || filters.studentsRange || filters.entityType || filters.entityValue) && (
        <div className="flex flex-wrap gap-2">
          {filters.search && (
            <Badge variant="secondary" className="cursor-pointer">
              🔍 {filters.search}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => {
                  setSearchQuery('')
                  handleFilterChange('search', undefined)
                }}
              />
            </Badge>
          )}
          {filters.category && (
            <Badge variant="secondary" className="cursor-pointer">
              📚 {filters.category}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('category', undefined)}
              />
            </Badge>
          )}
          {filters.estimatedWeeks && (
            <Badge variant="secondary" className="cursor-pointer">
              ⏱️ {filters.estimatedWeeks} {filters.estimatedWeeks === 1 ? 'semana' : 'semanas'}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('estimatedWeeks', undefined)}
              />
            </Badge>
          )}

          {filters.language && (
            <Badge variant="secondary" className="cursor-pointer">
              🌐 {filters.language}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('language', undefined)}
              />
            </Badge>
          )}
          {filters.currency && (
            <Badge variant="secondary" className="cursor-pointer">
              💱 {filters.currency}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('currency', undefined)}
              />
            </Badge>
          )}
          {filters.studentsRange && (
            <Badge variant="secondary" className="cursor-pointer">
              👥 {filters.studentsRange} estudiantes
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('studentsRange', undefined)}
              />
            </Badge>
          )}
          {filters.entityType && (
            <Badge variant="secondary" className="cursor-pointer">
              🏷️ {filters.entityType}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('entityType', undefined)}
              />
            </Badge>
          )}
          {filters.entityValue && (
            <Badge variant="secondary" className="cursor-pointer">
              🔖 {filters.entityValue}
              <X
                className="ml-1 h-3 w-3"
                onClick={() => handleFilterChange('entityValue', undefined)}
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
                <div className="h-40 bg-muted rounded" />
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
              {filters.search && courses[0]?.searchScore && (
                <span className="ml-2 text-xs">
                  (ordenado por relevancia)
                </span>
              )}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {courses.map((course) => (
              <Link 
                key={course._id} 
                href={`/courses/${course._id}${filters.search ? `?search=${encodeURIComponent(filters.search)}` : ''}`}
              >
                <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                  <CardHeader>
                    <img
                      src={course.image || '/placeholder-course.jpg'}
                      alt={course.title}
                      className="w-full h-40 object-cover rounded-md mb-2"
                    />
                    <CardTitle className="line-clamp-2">
                      <HighlightedText
                        text={course.title}
                        highlights={course.highlights}
                        path="title"
                      />
                    </CardTitle>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      <HighlightedText
                        text={course['short-description']}
                        highlights={course.highlights}
                        path="short-description"
                      />
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
                    {/* Mostrar entities si existen */}
                    {course.entities && course.entities.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {course.entities.slice(0, 3).map((entity: any, idx: number) => (
                          <Badge key={idx} variant="outline" className="text-xs truncate max-w-85">
                            {entity.type}: {entity.value}
                          </Badge>
                        ))}
                        {course.entities.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{course.entities.length - 3}
                          </Badge>
                        )}
                      </div>
                    )}

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