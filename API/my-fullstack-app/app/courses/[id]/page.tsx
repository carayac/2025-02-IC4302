import { notFound } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { BookOpen, Clock, Star, Calendar, Globe, GraduationCap, User, ArrowLeft, Play } from "lucide-react"
import Link from "next/link"

// Mock data - En producción esto vendría de una API o base de datos
const coursesData: Record<string, any> = {
  "1": {
    id: "1",
    title: "Desarrollo Web Full Stack con React y Node.js",
    description:
      "Aprende a construir aplicaciones web modernas desde cero. Este curso completo te llevará desde los fundamentos de HTML, CSS y JavaScript hasta la creación de aplicaciones full stack profesionales utilizando React para el frontend y Node.js con Express para el backend. Incluye proyectos prácticos, mejores prácticas de la industria y técnicas avanzadas de desarrollo.",
    category: "Programación",
    instructor: "María González",
    difficulty: "Intermedio",
    duration: "12 semanas",
    lessons: 48,
    rating: 4.8,
    reviewCount: 1234,
    date: "2024-01-15",
    language: "Español",
    price: 49.99,
    image: "/web-development-coding.png",
    learningPoints: [
      "Fundamentos de HTML5, CSS3 y JavaScript moderno",
      "React y sus hooks para interfaces dinámicas",
      "Node.js y Express para crear APIs RESTful",
      "Bases de datos con MongoDB",
      "Autenticación y autorización de usuarios",
      "Despliegue de aplicaciones en producción",
    ],
  },
  "2": {
    id: "2",
    title: "Machine Learning con Python",
    description:
      "Domina los conceptos fundamentales del aprendizaje automático y aplícalos usando Python. Aprenderás algoritmos de clasificación, regresión, clustering y redes neuronales.",
    category: "Ciencia",
    instructor: "Dr. Carlos Ruiz",
    difficulty: "Avanzado",
    duration: "16 semanas",
    lessons: 64,
    rating: 4.9,
    reviewCount: 892,
    date: "2024-02-01",
    language: "Español",
    price: 79.99,
    image: "/machine-learning-artificial-intelligence.jpg",
    learningPoints: [
      "Fundamentos de Machine Learning",
      "Algoritmos de clasificación y regresión",
      "Redes neuronales y Deep Learning",
      "Procesamiento de datos con Pandas",
      "Visualización con Matplotlib y Seaborn",
      "Proyectos reales de ML",
    ],
  },
  "3": {
    id: "3",
    title: "Diseño UX/UI Profesional",
    description:
      "Aprende a diseñar experiencias de usuario excepcionales. Desde la investigación hasta el prototipado y testing.",
    category: "Creativo",
    instructor: "Ana Martínez",
    difficulty: "Principiante",
    duration: "8 semanas",
    lessons: 32,
    rating: 4.7,
    reviewCount: 567,
    date: "2024-03-10",
    language: "Español",
    price: 39.99,
    image: "/ux-ui-design-interface.png",
    learningPoints: [
      "Principios de diseño UX/UI",
      "Investigación de usuarios",
      "Wireframing y prototipado",
      "Herramientas: Figma y Adobe XD",
      "Testing de usabilidad",
      "Portfolio profesional",
    ],
  },
}

// Cursos relacionados basados en categoría
const getRelatedCourses = (currentId: string, category: string) => {
  return Object.values(coursesData)
    .filter((course) => course.id !== currentId && course.category === category)
    .slice(0, 3)
}

const difficultyColors: Record<string, string> = {
  Principiante: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20",
  Intermedio: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20",
  Avanzado: "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20",
}

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const course = coursesData[id]

  if (!course) {
    notFound()
  }

  const relatedCourses = getRelatedCourses(course.id, course.category)

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
                  {course.category}
                </Badge>
                <h1 className="text-4xl font-bold tracking-tight text-balance lg:text-5xl">{course.title}</h1>
                <p className="text-lg text-muted-foreground text-pretty leading-relaxed">{course.description}</p>
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                  <span className="font-semibold">{course.rating}</span>
                  <span className="text-muted-foreground">({course.reviewCount} reseñas)</span>
                </div>
                <Separator orientation="vertical" className="h-5" />
                <div className="flex items-center gap-2 text-muted-foreground">
                  <User className="h-4 w-4" />
                  <span>{course.instructor}</span>
                </div>
                <Separator orientation="vertical" className="h-5" />
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>{new Date(course.date).toLocaleDateString("es-ES", { year: "numeric", month: "long" })}</span>
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
                      <span className="text-3xl font-bold">${course.price}</span>
                      <span className="text-sm text-muted-foreground">USD</span>
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
                        <GraduationCap className="h-4 w-4" />
                        <span>Dificultad</span>
                      </div>
                      <Badge variant="outline" className={difficultyColors[course.difficulty]}>
                        {course.difficulty}
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        <span>Duración</span>
                      </div>
                      <span className="font-medium">{course.duration}</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <BookOpen className="h-4 w-4" />
                        <span>Lecciones</span>
                      </div>
                      <span className="font-medium">{course.lessons} lecciones</span>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Globe className="h-4 w-4" />
                        <span>Idioma</span>
                      </div>
                      <span className="font-medium">{course.language}</span>
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
            {/* Lo que aprenderás */}
            <section className="space-y-4">
              <h2 className="text-2xl font-bold tracking-tight">Lo que aprenderás</h2>
              <Card className="border-border/50 bg-card/50">
                <CardContent className="pt-6">
                  <ul className="grid gap-3 sm:grid-cols-2">
                    {course.learningPoints.map((point: string, index: number) => (
                      <li key={index} className="flex gap-3">
                        <div className="mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10">
                          <div className="h-2 w-2 rounded-full bg-primary" />
                        </div>
                        <span className="text-sm leading-relaxed">{point}</span>
                      </li>
                    ))}
                  </ul>
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
                      <h3 className="font-semibold text-lg">{course.instructor}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Instructor profesional con más de 10 años de experiencia en la industria. Ha trabajado con
                        empresas líderes y ha ayudado a miles de estudiantes a alcanzar sus objetivos.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </section>
          </div>
        </div>

        {/* Cursos relacionados */}
        {relatedCourses.length > 0 && (
          <section className="mt-16 space-y-6">
            <div className="space-y-2">
              <h2 className="text-2xl font-bold tracking-tight">Cursos relacionados</h2>
              <p className="text-muted-foreground">Otros cursos que podrían interesarte</p>
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
                          <span className="font-medium">{relatedCourse.rating}</span>
                        </div>
                        <span className="text-sm font-semibold">${relatedCourse.price}</span>
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
