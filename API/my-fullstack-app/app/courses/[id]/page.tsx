import { notFound } from 'next/navigation'
import { fetchCourse, formatPrice, formatStudents } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Navbar } from '@/components/home/navbar'
import { HighlightedText } from '@/components/ui/highlighted-text'
import Link from 'next/link'
import { Star, Users, Globe, DollarSign, Award, MessageSquare } from 'lucide-react'

interface CoursePageProps {
  params: Promise<{ id: string }>
  searchParams: Promise<{ search?: string }>
}

export default async function CoursePage({ params, searchParams }: CoursePageProps) {
  const { id } = await params
  const { search } = await searchParams

  try {
    const response = await fetchCourse(id, search)

    if (!response.success) {
      notFound()
    }

    const course = response.data

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-white">
        <Navbar />
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          {/* Header Section */}
          <div className="mb-8">
            <div className="flex flex-wrap gap-2 mb-4">
              <Badge variant="secondary" className="text-sm">
                {course.general_category}
              </Badge>
              {course.specific_category && (
                <Badge variant="outline" className="text-sm">
                  {course.specific_category}
                </Badge>
              )}
              <Badge variant="outline" className="text-sm">
                <Globe className="w-3 h-3 mr-1" />
                {course.language}
              </Badge>
              <Badge variant="outline" className="text-sm">
                <DollarSign className="w-3 h-3 mr-1" />
                {course.currency}
              </Badge>
            </div>

            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight">
              <HighlightedText
                text={course.title}
                highlights={course.highlights}
                path="title"
              />
            </h1>

            <div className="flex flex-wrap items-center gap-6 text-gray-600">
              <div className="flex items-center gap-1">
                <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                <span className="font-semibold">{course.rating_value.toFixed(1)}</span>
                <span className="text-sm">({course.reviewStats?.totalReviews || 0} reviews)</span>
              </div>
              <div className="flex items-center gap-1">
                <Users className="w-5 h-5" />
                <span>{formatStudents(course.students)} estudiantes</span>
              </div>
            </div>
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Course Image */}
              <Card className="overflow-hidden shadow-lg">
                <CardContent className="p-0">
                  <img
                    src={course.image || '/placeholder-course.jpg'}
                    alt={course.title}
                    className="w-full h-64 md:h-80 object-cover"
                  />
                </CardContent>
              </Card>

              {/* Course Description */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-xl">
                    <MessageSquare className="w-5 h-5" />
                    Descripción del Curso
                  </CardTitle>
                </CardHeader>
                <CardContent className="prose max-w-none text-gray-700 leading-relaxed">
                  <HighlightedText
                    text={course.description}
                    highlights={course.highlights}
                    path="description"
                  />
                </CardContent>
              </Card>

              {/* Author Comment */}
              {course.authorComment && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <Award className="w-5 h-5" />
                      Comentario del Instructor
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="prose max-w-none text-gray-700 leading-relaxed">
                    <HighlightedText
                      text={course.authorComment}
                      highlights={course.highlights}
                      path="authorComment"
                    />
                  </CardContent>
                </Card>
              )}

              {/* Certificate Info */}
              {course.certificate_info && (
                <Card className="shadow-lg border-green-200 bg-green-50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xl text-green-800">
                      <Award className="w-5 h-5 text-green-600" />
                      Certificación
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-green-700">{course.certificate_info}</p>
                  </CardContent>
                </Card>
              )}

              {/* Entities */}
              {course.entities && course.entities.length > 0 && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-xl">Entidades Mencionadas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {course.entities.map((entity: any, idx: number) => (
                        <Badge key={idx} variant="outline" className="text-sm">
                          {entity.type}: {entity.value}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Reviews */}
              {course.reviews && course.reviews.length > 0 && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                      Reviews y Comentarios ({course.reviewStats?.totalReviews || 0})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {course.reviews.slice(0, 10).map((review: any, idx: number) => (
                        <div key={idx} className="border-b border-gray-100 pb-6 last:border-b-0 last:pb-0">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                                {(review.author || 'Anon').charAt(0).toUpperCase()}
                              </div>
                              <div>
                                <p className="font-semibold text-gray-900">
                                  {review.author || 'Usuario Anónimo'}
                                </p>
                                <div className="flex items-center gap-1">
                                  {[...Array(5)].map((_, i) => (
                                    <Star
                                      key={i}
                                      className={`w-4 h-4 ${
                                        i < review.rating
                                          ? 'fill-yellow-400 text-yellow-400'
                                          : 'text-gray-300'
                                      }`}
                                    />
                                  ))}
                                  <span className="text-sm text-gray-500 ml-1">
                                    {review.rating}/5
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                          <p className="text-gray-700 leading-relaxed pl-13">
                            {review.comment}
                          </p>
                        </div>
                      ))}
                      {course.reviews.length > 10 && (
                        <div className="text-center pt-4">
                          <p className="text-gray-500 text-sm">
                            Y {course.reviews.length - 10} reviews más...
                          </p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Course Info & Purchase */}
              <Card className="shadow-lg sticky top-4">
                <CardHeader>
                  <CardTitle className="text-xl">Información del Curso</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Price */}
                  <div className="text-center">
                    <div className="text-4xl font-bold text-gray-900 mb-2">
                      {formatPrice(course.price, course.currency)}
                    </div>
                    <button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 font-semibold shadow-md hover:shadow-lg transform hover:-translate-y-0.5">
                      Comprar Ahora
                    </button>
                  </div>

                  {/* Course Stats */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between py-2 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <Star className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm font-medium">Rating</span>
                      </div>
                      <span className="font-semibold">{course.rating_value.toFixed(1)}</span>
                    </div>

                    <div className="flex items-center justify-between py-2 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-medium">Estudiantes</span>
                      </div>
                      <span className="font-semibold">{formatStudents(course.students)}</span>
                    </div>

                    <div className="flex items-center justify-between py-2 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-green-500" />
                        <span className="text-sm font-medium">Idioma</span>
                      </div>
                      <span className="font-semibold">{course.language}</span>
                    </div>

                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-purple-500" />
                        <span className="text-sm font-medium">Moneda</span>
                      </div>
                      <span className="font-semibold">{course.currency}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Rating Distribution */}
              {course.reviewStats && (
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-lg">Distribución de Calificaciones</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[5, 4, 3, 2, 1].map((rating) => {
                        const count = course.reviewStats.ratingDistribution[rating] || 0
                        const maxCount = Math.max(...(Object.values(course.reviewStats.ratingDistribution) as number[]))
                        const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0

                        return (
                          <div key={rating} className="flex items-center gap-3">
                            <div className="flex items-center gap-1 min-w-[60px]">
                              <span className="text-sm font-medium">{rating}</span>
                              <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                            </div>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-yellow-400 to-yellow-500 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-500 min-w-[30px] text-right">
                              {count}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {/* Related Products */}
          {course.relatedProducts && course.relatedProducts.length > 0 && (
            <div className="mt-16">
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">Productos Relacionados</h2>
                <p className="text-gray-600">Cursos que podrían interesarte</p>
              </div>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {course.relatedProducts.map((product: any) => (
                  <Link
                    key={product.id}
                    href={`/courses/${product.originalCourseId}?search=${search || ''}`}
                    className="block group"
                  >
                    <Card className="h-full hover:shadow-xl transition-all duration-300 border-0 shadow-md group-hover:-translate-y-1">
                      <CardHeader className="pb-3">
                        <div className="relative overflow-hidden rounded-lg mb-3">
                          <img
                            src={product.image || '/placeholder-course.jpg'}
                            alt={product.title}
                            className="w-full h-32 object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        </div>
                        <CardTitle className="text-sm line-clamp-2 group-hover:text-blue-600 transition-colors">
                          {product.title}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="pt-0 space-y-3">
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                            <span>{product.rating_value?.toFixed(1) || 'N/A'}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            <span>{formatStudents(product.students || 0)}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <Badge variant="secondary" className="text-xs">
                            {product.general_category}
                          </Badge>
                          <span className="font-bold text-sm text-gray-900">
                            {formatPrice(product.price || 0, product.currency)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 line-clamp-2">
                          {product.short_description}
                        </p>
                        <Badge variant="outline" className="text-xs w-full justify-center border-dashed">
                          Ver curso relacionado
                        </Badge>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  } catch (error) {
    console.error('Error loading course:', error)
    notFound()
  }
}