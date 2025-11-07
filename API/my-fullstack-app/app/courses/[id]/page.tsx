import { notFound } from 'next/navigation'
import { fetchCourse, formatPrice, formatStudents } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Navbar } from '@/components/home/navbar'
import { Button } from '@/components/ui/button'
import { HighlightedText } from '@/components/ui/highlighted-text'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export const dynamic = 'force-dynamic'

export default async function CoursePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>
  searchParams: Promise<{ search?: string }>
}) {
  const { id } = await params
  const { search } = await searchParams

  let course: any = null

  try {
    const response = await fetchCourse(id, search)
    course = response.data
  } catch (error) {
    console.error('Error loading course:', error)
    notFound()
  }

  if (!course) {
    notFound()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/80">
      <Navbar />
      <div className="p-4">
        <div className="mx-auto max-w-4xl">
          <Link href={`/${search ? `?search=${encodeURIComponent(search)}` : ''}`}>
            <Button variant="ghost" className="mb-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver a cursos
            </Button>
          </Link>

          <Card>
            <CardHeader>
              <img
                src={course.image || '/placeholder-course.jpg'}
                alt={course.title}
                className="w-full h-80 md:h-96 object-cover rounded-md mb-4"
              />
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <CardTitle className="text-3xl mb-2">
                    <HighlightedText
                      text={course.title}
                      highlights={course.highlights}
                      path="title"
                    />
                  </CardTitle>
                  <p className="text-lg text-muted-foreground">
                    <HighlightedText
                      text={course['short-description']}
                      highlights={course.highlights}
                      path="short-description"
                    />
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold">
                    {formatPrice(course.price, course.currency)}
                  </p>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold">⭐ {course.rating_value.toFixed(1)}</p>
                  <p className="text-sm text-muted-foreground">Rating</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">👥 {formatStudents(course.students)}</p>
                  <p className="text-sm text-muted-foreground">Estudiantes</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">💬 {course.reviewStats.totalReviews}</p>
                  <p className="text-sm text-muted-foreground">Reviews</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">🌐 {course.language}</p>
                  <p className="text-sm text-muted-foreground">Idioma</p>
                </div>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <Badge>{course.general_category}</Badge>
                <Badge variant="outline">🌐 {course.language}</Badge>
                {search && (
                  <Badge variant="secondary">
                    🔍 Búsqueda: {search}
                  </Badge>
                )}
              </div>

              {/* Certificate Info - Sección separada */}
              {course.certificate_info && (
                <div>
                  <h3 className="text-xl font-semibold mb-2">Certificación</h3>
                  <p className="text-muted-foreground break-words">
                    📜 {course.certificate_info}
                  </p>
                </div>
              )}

              {/* Description */}
              {course.description && (
                <div>
                  <h3 className="text-xl font-semibold mb-2">Descripción</h3>
                  <p className="text-muted-foreground whitespace-pre-line">
                    <HighlightedText
                      text={course.description}
                      highlights={course.highlights}
                      path="description"
                    />
                  </p>
                </div>
              )}

              {/* Author Comment */}
              {course.authorComment && (
                <div>
                  <h3 className="text-xl font-semibold mb-2">Comentario del Instructor</h3>
                  <p className="text-muted-foreground">
                    <HighlightedText
                      text={course.authorComment}
                      highlights={course.highlights}
                      path="authorComment"
                    />
                  </p>
                </div>
              )}

              {/* Rating Distribution */}
              <div>
                <h3 className="text-xl font-semibold mb-4">Distribución de Ratings</h3>
                <div className="space-y-2">
                  {[5, 4, 3, 2, 1].map((stars) => {
                    const count = course.reviewStats.ratingDistribution[stars] || 0
                    const percentage = course.reviewStats.totalReviews > 0
                      ? (count / course.reviewStats.totalReviews) * 100
                      : 0
                    return (
                      <div key={stars} className="flex items-center gap-2">
                        <span className="w-12">{stars} ⭐</span>
                        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <span className="w-12 text-sm text-muted-foreground">
                          {count}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Reviews */}
              {course.reviews && course.reviews.length > 0 && (
                <div>
                  <h3 className="text-xl font-semibold mb-4">Reviews Recientes</h3>
                  <div className="space-y-4">
                    {course.reviews.slice(0, 5).map((review: any, index: number) => (
                      <Card key={index}>
                        <CardContent className="pt-4">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-semibold">{review.user}</span>
                            <div className="flex items-center gap-1">
                              <span>{'⭐'.repeat(review.rating)}</span>
                              <span className="text-sm text-muted-foreground ml-1">
                                {review.date}
                              </span>
                            </div>
                          </div>
                          {review.comment && (
                            <p className="text-muted-foreground">{review.comment}</p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}