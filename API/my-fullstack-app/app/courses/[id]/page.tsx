import { notFound } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Star, Calendar, Globe, User, ArrowLeft, Play, Users, Award } from "lucide-react"
import Link from "next/link"

const coursesData: Record<string, any> = {
  "1": {
    id: "1",
    title: "Curso de C#",
    general_category: "Programación",
    specific_category: null,
    description:
      "Este curso de C# está dirigido a programadores principiantes y avanzados, así como a estudiantes de informática que deseen aprender a programar en C#, uno de los lenguajes de programación más utilizados para el desarrollo de aplicaciones en plataformas Windows. Este curso de C# incluye un proyecto práctico con el que podrás desarrollar una aplicación de escritorio utilizando C#.",
    image: "https://d3puay5pkxu9s4.cloudfront.net/courses/12632/img/web/800_imagen.jpg",
    price: 0.0,
    currency: "USD",
    language: "es",
    students: 3947,
    certificate_info:
      "Puedes compartir tu Certificado en LinkedIn, en tu currículum impreso o en otros documentos. Obtenga un certificado de estudios Validez internacional Evidencie su aprendizaje ante cualquier empleador o institución. Tareas calificadas Reciba calificaciones y observaciones de todas sus actividades resueltas. Asistencia académica Solicite asesoría sobre su proceso de certificación. C# Language Programmer 120 horas certificables Al finalizar el Curso de C# puede obtener un certificado de estudios para evidenciar sus nuevos conocimientos y habilidades.",
    authorComment: "Sergio Obredor Arquitecto de Infraestructura en la Nube, Equipo de TI en Edutin Academy Profesor",
    reviews: [
      {
        user: "Fabian",
        comment: "cool",
        rating: 5.0,
        date: "07/09/2025",
      },
      {
        user: "Inti",
        comment: null,
        rating: 5.0,
        date: "30/08/2025",
      },
      {
        user: "Antonio",
        comment:
          "Lo he utilizado a modo de repaso ya que realice mis practicas de DAM en C# y tengo varios proyectos en mi GitHub en C# también, pero tras una temporada sin usarlo mucho me ha servido para refrescar un poco todo.",
        rating: 5.0,
        date: "18/08/2025",
      },
    ],
    rating_value: 5.0,
    date_extracted: "03/11/2025",
  },
  "2": {
    id: "2",
    title: "Curso de oftalmología",
    general_category: "Salud",
    specific_category: null,
    description:
      "Este curso de oftalmología está dirigido a médicos, residentes en oftalmología, optómetras, estudiantes de medicina y personal relacionado al área de la salud que desean desarrollar conocimientos y habilidades en el campo de la oftalmología y brindar un cuidado integral y de calidad a sus pacientes. Este curso de oftalmología incluye actividades prácticas basadas en casos clínicos.",
    image: "https://d3puay5pkxu9s4.cloudfront.net/courses/12559/img/web/800_imagen.jpg",
    price: 0.0,
    currency: "USD",
    language: "es",
    students: 1138,
    certificate_info:
      "Puedes compartir tu Certificado en LinkedIn, en tu currículum impreso o en otros documentos. Validez internacional Tareas calificadas Asistencia académica Actualización en Oftalmología Clínica 120 horas certificables",
    authorComment:
      "Este curso de oftalmología ha sido estructurado pedagógicamente mediante recursos educativos compartidos directamente desde YouTube, bajo Licencia YouTube Estándar.",
    reviews: [
      {
        user: "Marybel",
        comment:
          "Fundamental, para seguir aprendiendo y dar un mejor servicio de información y consulta a mis pacientes., gracias 10 de 10",
        rating: 5.0,
        date: "17/10/2025",
      },
      {
        user: "Yanelkys",
        comment: null,
        rating: 5.0,
        date: "18/09/2025",
      },
      {
        user: "Any",
        comment: "Me encanta tener nuevos conocimientos",
        rating: 5.0,
        date: "21/08/2025",
      },
    ],
    rating_value: 4.9,
    date_extracted: "03/11/2025",
  },
}

const getRelatedCourses = (currentId: string, category: string) => {
  return Object.values(coursesData)
    .filter((course) => course.id !== currentId && course.general_category === category)
    .slice(0, 3)
}

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const course = coursesData[id]

  if (!course) {
    notFound()
  }

  const relatedCourses = getRelatedCourses(course.id, course.general_category)
  const ratingPercentage = (course.rating_value / 5) * 100

  return (
    <main className="min-h-screen bg-background">
      {/* Header con navegación */}
      <div className="border-b bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Volver a cursos
            </Button>
          </Link>
        </div>
      </div>

      {/* Hero Section */}
      <div className="border-b bg-gradient-to-b from-muted/50 to-background">
        <div className="container mx-auto px-4 py-12">
          <div className="grid gap-8 lg:grid-cols-3">
            {/* Información principal */}
            <div className="space-y-6 lg:col-span-2">
              <div className="space-y-4">
                <Badge variant="outline" className="w-fit">
                  {course.general_category}
                </Badge>
                <h1 className="text-4xl font-bold tracking-tight text-balance lg:text-5xl">{course.title}</h1>
                <p className="text-lg text-muted-foreground text-pretty leading-relaxed">{course.description}</p>
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                  <span className="font-semibold">{course.rating_value}</span>
                  <span className="text-muted-foreground">({course.reviews.length} reseñas)</span>
                </div>
                <Separator orientation="vertical" className="h-5" />
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Users className="h-4 w-4" />
                  <span>{course.students.toLocaleString()} estudiantes</span>
                </div>
                <Separator orientation="vertical" className="h-5" />
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Globe className="h-4 w-4" />
                  <span>{course.language.toUpperCase()}</span>
                </div>
                <Separator orientation="vertical" className="h-5" />
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>
                    {new Date(course.date_extracted).toLocaleDateString("es-ES", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}
                  </span>
                </div>
              </div>
            </div>

            {/* Card de inscripción */}
            <div className="lg:col-span-1">
              <Card className="sticky top-4 border-border/50 bg-card/80 backdrop-blur-sm">
                <CardHeader className="space-y-4">
                  <div className="aspect-video overflow-hidden rounded-lg bg-gradient-to-br from-primary/20 to-primary/5">
                    <img
                      src={course.image || "/placeholder.svg"}
                      alt={course.title}
                      className="h-full w-full object-cover"
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">{course.price === 0 ? "Gratis" : `$${course.price}`}</span>
                      {course.price > 0 && <span className="text-sm text-muted-foreground">{course.currency}</span>}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button className="w-full gap-2" size="lg">
                    <Play className="h-4 w-4" />
                    Inscribirse ahora
                  </Button>

                  <Separator />

                  <div className="space-y-3 text-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Users className="h-4 w-4" />
                        <span>Estudiantes</span>
                      </div>
                      <span className="font-medium">{course.students.toLocaleString()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Globe className="h-4 w-4" />
                        <span>Idioma</span>
                      </div>
                      <span className="font-medium">{course.language.toUpperCase()}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Award className="h-4 w-4" />
                        <span>Rating</span>
                      </div>
                      <span className="font-medium">{course.rating_value}/5.0</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid gap-12 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-2">
            {/* Información del certificado */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold tracking-tight">Certificación</h2>
              <Card className="border-border/50 bg-card/50">
                <CardContent className="pt-6">
                  <p className="text-sm leading-relaxed text-muted-foreground">{course.certificate_info}</p>
                </CardContent>
              </Card>
            </section>

            {/* Sobre el instructor */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold tracking-tight">Sobre el instructor</h2>
              <Card className="border-border/50 bg-card/50">
                <CardContent className="pt-6">
                  <div className="flex gap-4">
                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5">
                      <User className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-semibold text-lg">Instructor del Curso</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">{course.authorComment}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>

            {/* Reseñas */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold tracking-tight">Reseñas de estudiantes</h2>
              <div className="space-y-3">
                {course.reviews.map((review: any, index: number) => (
                  <Card key={index} className="border-border/50 bg-card/50">
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">{review.user}</h4>
                          <div className="flex items-center gap-1">
                            {[...Array(Math.round(review.rating))].map((_, i) => (
                              <Star key={i} className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                            ))}
                          </div>
                        </div>
                        {review.comment && <p className="text-sm text-muted-foreground">{review.comment}</p>}
                        <p className="text-xs text-muted-foreground/70">{review.date}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          </div>
        </div>

        {/* Cursos relacionados */}
        {relatedCourses.length > 0 && (
          <section className="mt-16 space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight">Cursos relacionados</h2>
              <p className="text-muted-foreground">Otros cursos de {course.general_category} que podrían interesarte</p>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {relatedCourses.map((relatedCourse) => (
                <Link key={relatedCourse.id} href={`/courses/${relatedCourse.id}`}>
                  <Card className="group h-full cursor-pointer border-border/50 bg-card/50 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg">
                    <CardHeader>
                      <div className="mb-3 aspect-video overflow-hidden rounded-md bg-gradient-to-br from-primary/20 to-primary/5">
                        <img
                          src={relatedCourse.image || "/placeholder.svg"}
                          alt={relatedCourse.title}
                          className="h-full w-full object-cover transition-transform group-hover:scale-105"
                        />
                      </div>
                      <CardTitle className="line-clamp-2 text-lg">{relatedCourse.title}</CardTitle>
                      <CardDescription className="line-clamp-2">{relatedCourse.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1 text-sm">
                          <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                          <span className="font-medium">{relatedCourse.rating_value}</span>
                        </div>
                        <span className="text-sm font-semibold">
                          {relatedCourse.price === 0 ? "Gratis" : `$${relatedCourse.price}`}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  )
}
