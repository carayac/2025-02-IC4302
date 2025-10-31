"use client"

import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Search, SlidersHorizontal, X, Star } from "lucide-react"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import Link from "next/link"

const categories = [
  { id: "programacion", label: "Programación", group: "Tecnología" },
  { id: "cloud", label: "Cloud Computing", group: "Tecnología" },
  { id: "ciencia", label: "Ciencia", group: "Académico" },
  { id: "idiomas", label: "Idiomas", group: "Académico" },
  { id: "psicologia", label: "Psicología", group: "Académico" },
  { id: "negocio", label: "Negocio", group: "Profesional" },
  { id: "marketing", label: "Marketing", group: "Profesional" },
  { id: "cocina", label: "Cocina", group: "Estilo de Vida" },
  { id: "salud", label: "Salud", group: "Estilo de Vida" },
  { id: "deporte", label: "Deporte", group: "Estilo de Vida" },
  { id: "creativo", label: "Creativo", group: "Arte y Diseño" },
  { id: "arte", label: "Arte", group: "Arte y Diseño" },
  { id: "moda", label: "Moda", group: "Arte y Diseño" },
  { id: "mantenimiento", label: "Mantenimiento", group: "Otros" },
]

const groupedCategories = categories.reduce(
  (acc, category) => {
    if (!acc[category.group]) {
      acc[category.group] = []
    }
    acc[category.group].push(category)
    return acc
  },
  {} as Record<string, typeof categories>,
)

const mockCourses = [
  {
    id: "1",
    title: "Desarrollo Web Full Stack con React y Node.js",
    description: "Aprende a construir aplicaciones web modernas desde cero con React y Node.js",
    category: "Programación",
    price: 49.99,
    rating: 4.8,
    image: "/web-development-coding.png",
  },
  {
    id: "2",
    title: "Machine Learning con Python",
    description: "Domina los conceptos fundamentales del aprendizaje automático y aplícalos usando Python",
    category: "Ciencia",
    price: 79.99,
    rating: 4.9,
    image: "/machine-learning-artificial-intelligence.jpg",
  },
  {
    id: "3",
    title: "Diseño UX/UI Profesional",
    description: "Aprende a diseñar experiencias de usuario excepcionales desde la investigación hasta el prototipado",
    category: "Creativo",
    price: 39.99,
    rating: 4.7,
    image: "/ux-ui-design-interface.png",
  },
  {
    id: "4",
    title: "Marketing Digital Avanzado",
    description: "Estrategias modernas de marketing digital para hacer crecer tu negocio online",
    category: "Marketing",
    price: 59.99,
    rating: 4.6,
    image: "/digital-marketing-social-media.png",
  },
  {
    id: "5",
    title: "Cloud Computing con AWS",
    description: "Aprende a diseñar y desplegar aplicaciones escalables en Amazon Web Services",
    category: "Cloud Computing",
    price: 69.99,
    rating: 4.8,
    image: "/cloud-computing-aws-servers.jpg",
  },
  {
    id: "6",
    title: "Inglés para Negocios",
    description: "Mejora tu inglés profesional para destacar en el mundo empresarial internacional",
    category: "Idiomas",
    price: 44.99,
    rating: 4.5,
    image: "/business-english-language-learning.jpg",
  },
]

export function CourseSearch() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false)

  const handleCategoryToggle = (categoryId: string) => {
    setSelectedCategories((prev) =>
      prev.includes(categoryId) ? prev.filter((id) => id !== categoryId) : [...prev, categoryId],
    )
  }

  const handleRemoveCategory = (categoryId: string) => {
    setSelectedCategories((prev) => prev.filter((id) => id !== categoryId))
  }

  const handleClearFilters = () => {
    setSelectedCategories([])
  }

  const handleSearch = () => {
    console.log("[v0] Searching for:", searchQuery, "Categories:", selectedCategories)
    // Aquí implementarías la lógica de búsqueda
  }

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar cursos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10"
              />
            </div>
            <Sheet open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="relative shrink-0 bg-transparent">
                  <SlidersHorizontal className="h-4 w-4" />
                  {selectedCategories.length > 0 && (
                    <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-semibold text-primary-foreground">
                      {selectedCategories.length}
                    </span>
                  )}
                </Button>
              </SheetTrigger>
              <SheetContent className="w-full sm:max-w-md">
                <SheetHeader className="space-y-3 pb-6">
                  <div className="flex items-center justify-between">
                    <SheetTitle className="text-2xl">Filtros</SheetTitle>
                    {selectedCategories.length > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {selectedCategories.length} seleccionado{selectedCategories.length !== 1 ? "s" : ""}
                      </Badge>
                    )}
                  </div>
                  <SheetDescription className="text-balance">
                    Refina tu búsqueda seleccionando las categorías que te interesan
                  </SheetDescription>
                </SheetHeader>

                <Separator className="my-4" />

                <ScrollArea className="h-[calc(100vh-280px)] pr-4">
                  <div className="space-y-6">
                    {Object.entries(groupedCategories).map(([group, groupCategories]) => (
                      <div key={group} className="space-y-3">
                        <h3 className="text-sm font-semibold tracking-tight text-foreground">{group}</h3>
                        <div className="space-y-2">
                          {groupCategories.map((category) => (
                            <div
                              key={category.id}
                              className="group flex items-center gap-3 rounded-lg border border-transparent p-2 transition-colors hover:border-border hover:bg-accent/50"
                            >
                              <Checkbox
                                id={category.id}
                                checked={selectedCategories.includes(category.id)}
                                onCheckedChange={() => handleCategoryToggle(category.id)}
                                className="data-[state=checked]:border-primary data-[state=checked]:bg-primary"
                              />
                              <Label
                                htmlFor={category.id}
                                className="flex-1 cursor-pointer text-sm font-medium leading-none transition-colors group-hover:text-foreground peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                              >
                                {category.label}
                              </Label>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>

                <Separator className="my-4" />

                <div className="flex gap-2">
                  {selectedCategories.length > 0 && (
                    <Button
                      variant="outline"
                      onClick={handleClearFilters}
                      className="flex-1 transition-all hover:bg-destructive/10 hover:text-destructive bg-transparent"
                    >
                      Limpiar
                    </Button>
                  )}
                  <Button
                    onClick={() => {
                      handleSearch()
                      setIsAdvancedOpen(false)
                    }}
                    className="flex-1"
                  >
                    Aplicar filtros
                  </Button>
                </div>
              </SheetContent>
            </Sheet>
            <Button onClick={handleSearch}>Buscar</Button>
          </div>

          {/* Active Filters */}
          {selectedCategories.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {selectedCategories.map((categoryId) => {
                const category = categories.find((c) => c.id === categoryId)
                return (
                  <Badge key={categoryId} variant="secondary" className="gap-1 pr-1">
                    {category?.label}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 rounded-full hover:bg-background/80"
                      onClick={() => handleRemoveCategory(categoryId)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Search Results */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {mockCourses.map((course) => (
          <Link key={course.id} href={`/courses/${course.id}`}>
            <Card className="group h-full cursor-pointer border-border/50 bg-card/50 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg">
              <CardHeader>
                <div className="mb-3 aspect-video overflow-hidden rounded-md bg-gradient-to-br from-primary/20 to-primary/5">
                  <img
                    src={course.image || "/placeholder.svg"}
                    alt={course.title}
                    className="h-full w-full object-cover transition-transform group-hover:scale-105"
                  />
                </div>
                <CardTitle className="line-clamp-2 text-lg group-hover:text-primary transition-colors">
                  {course.title}
                </CardTitle>
                <CardDescription className="line-clamp-2">{course.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="text-xs">
                      {course.category}
                    </Badge>
                    <div className="flex items-center gap-1 text-sm">
                      <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                      <span className="font-medium">{course.rating}</span>
                    </div>
                  </div>
                  <span className="text-sm font-semibold">${course.price}</span>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
