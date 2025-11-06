import { Navbar } from "@/components/home/navbar"
import { CourseSearch } from "@/components/home/course-search"
import connectDB from "@/lib/mongoose"
import Course from "@/lib/models/course"

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  // Obtener categorías e idiomas únicos para los filtros
  let categories: string[] = []
  let languages: string[] = []
  let totalCourses = 0

  try {
    await connectDB()
    
    // Obtener categorías únicas
    categories = await Course.distinct('general_category')
    categories = categories.filter(Boolean).sort()
    
    // Obtener idiomas únicos
    languages = await Course.distinct('language')
    languages = languages.filter(Boolean).sort()
    
    // Contar total de cursos
    totalCourses = await Course.countDocuments()
  } catch (error) {
    console.error('Error loading initial data:', error)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/80">
      <Navbar />
      <div className="p-4">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold">Buscar Cursos</h1>
            <p className="text-muted-foreground">
              Encuentra el curso perfecto para ti.
              {totalCourses > 0 && ` ${totalCourses.toLocaleString()} cursos disponibles.`}
            </p>
          </div>
          <CourseSearch 
            initialCategories={categories}
            initialLanguages={languages}
          />
        </div>
      </div>
    </div>
  )
}