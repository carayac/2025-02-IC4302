import { Navbar } from "@/components/home/navbar";
import { CourseSearch } from "@/components/home/course-search";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/80">
      <Navbar /> {/* Navbar con logout */}
      <div className="p-4">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8">
            <h1 className="text-3xl font-bold">Buscar Cursos</h1>
            <p className="text-muted-foreground">Encuentra el curso perfecto para ti.</p>
          </div>
          <CourseSearch /> {/* Componente de búsqueda normal y avanzada */}
        </div>
      </div>
    </div>
  );
}