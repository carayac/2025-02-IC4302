import { NextRequest, NextResponse } from 'next/server'
import connectDB from '@/lib/mongoose'
import Course from '@/lib/models/course'
import mongoose from 'mongoose'
import { authAdmin } from '@/lib/firebase-admin'

export const dynamic = 'force-dynamic'


export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { searchParams } = new URL(request.url)
    const searchQuery = searchParams.get('search') || ''

    // Validar que el ID sea un ObjectId válido de MongoDB
    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        {
          success: false,
          error: 'ID de curso inválido',
          message: 'El ID proporcionado no tiene el formato correcto de MongoDB ObjectId',
        },
        { status: 400 }
      )
    }

  
    // Verifica si tiene token de autenticación
    const token = request.cookies.get('auth-token')?.value
    console.log('Token recibido:', token ? 'Presente' : 'Ausente')  

    if (!token) {
      return NextResponse.json({ success: false, error: 'No autorizado' }, { status: 401 })
    }

    // Verifica si el token fue emitido por Firebase
    const decodedToken = await authAdmin.verifyIdToken(token)
    console.log('Token decodificado ahora siuuu (UID):', decodedToken?.uid)  

    if (!decodedToken) {
      return NextResponse.json({ success: false, error: 'El token no es válido' }, { status: 401 })
    }

    // Conectar a la base de datos
    await connectDB()

    let course: any = null
    let highlights: any = null

    // Si hay búsqueda, usar Atlas Search con highlighting
    if (searchQuery) {
      const pipeline = [
        {
          $search: {
            index: 'default',
            compound: {
              must: [
                {
                  equals: {
                    path: '_id',
                    value: new mongoose.Types.ObjectId(id)
                  }
                }
              ],
              should: [
                {
                  text: {
                    query: searchQuery,
                    path: ['title', 'description', 'short-description', 'authorComment'],
                    fuzzy: {
                      maxEdits: 2,
                      prefixLength: 3
                    }
                  }
                }
              ]
            },
            highlight: {
              path: ['title', 'description', 'short-description', 'authorComment']
            }
          }
        },
        {
          $addFields: {
            highlights: { $meta: 'searchHighlights' }
          }
        },
        {
          $project: { __v: 0 }
        }
      ]

      const results = await Course.aggregate(pipeline)
      course = results[0] || null
      highlights = course?.highlights
    } else {
      // Sin búsqueda, usar findById normal
      course = await Course.findById(id)
        .select('-__v')
        .lean()
    }

    // Verificar si el curso existe
    if (!course) {
      return NextResponse.json(
        {
          success: false,
          error: 'Curso no encontrado',
          message: `No se encontró ningún curso con el ID: ${id}`,
        },
        { status: 404 }
      )
    }

    // Función para buscar cursos relacionados por título
    async function findRelatedCoursesByTitle(relatedProductsData: any[]) {
      const relatedTitles = relatedProductsData
        .map((p: any) => p.title || p.authorComment?.substring(0, 100))
        .filter(Boolean)
        .filter((title, index, arr) => arr.indexOf(title) === index) // Remover duplicados

      if (relatedTitles.length === 0) return []

      try {
        // Buscar cursos que coincidan con los títulos
        const relatedCourses = await Course.find({
          $or: [
            { title: { $in: relatedTitles } },
            // También buscar por authorComment si contiene el título
            ...relatedTitles.map(title => ({
              authorComment: { $regex: title.substring(0, 50), $options: 'i' }
            }))
          ],
          _id: { $ne: course._id } // Excluir el curso actual
        })
        .select('title image rating_value students general_category language currency price _id')
        .limit(20)
        .lean()

        // Mapear los resultados con los datos originales
        return relatedCourses.map((relatedCourse: any) => {
          // Encontrar el producto relacionado original que coincide
          const originalProduct = relatedProductsData.find((p: any) =>
            p.title === relatedCourse.title ||
            (p.authorComment && relatedCourse.title.includes(p.authorComment.substring(0, 50)))
          )

          return {
            id: relatedCourse._id.toString(),
            title: relatedCourse.title,
            price: relatedCourse.price || 0,
            currency: relatedCourse.currency || 'USD',
            image: relatedCourse.image || course.image || '/placeholder-course.jpg',
            rating_value: relatedCourse.rating_value || 0,
            students: relatedCourse.students || 0,
            general_category: relatedCourse.general_category || course.general_category,
            language: relatedCourse.language || course.language,
            short_description: originalProduct?.description?.substring(0, 200) + '...' ||
                            originalProduct?.short_description ||
                            relatedCourse.title,
            // Marcar como producto relacionado
            isRelated: true,
            originalCourseId: relatedCourse._id.toString()
          }
        })
      } catch (error) {
        console.warn('Error buscando cursos relacionados por título:', error)
        return []
      }
    }

    // Obtener productos relacionados
    let relatedProducts: any[] = []
    if (course.productos_relacionados && course.productos_relacionados.length > 0) {
      try {
        // Intentar buscar cursos reales por título primero
        relatedProducts = await findRelatedCoursesByTitle(course.productos_relacionados)

        // Si no encontramos cursos reales, usar los datos embebidos como fallback
        if (relatedProducts.length === 0) {
          console.log('No se encontraron cursos reales, usando datos embebidos como fallback')
          relatedProducts = course.productos_relacionados.map((product: any, index: number) => ({
            id: `fallback_${course._id}_${index}`,
            title: product.title || product.authorComment?.substring(0, 100) + '...' || 'Producto relacionado',
            price: product.price || 0,
            currency: product.currency || 'USD',
            image: product.image || course.image || '/placeholder-course.jpg',
            rating_value: product.rating_value || course.rating_value || 0,
            students: product.students || course.students || 0,
            general_category: product.general_category || course.general_category,
            language: product.language || course.language,
            short_description: product.description?.substring(0, 200) + '...' || '',
            // Marcar como producto relacionado
            isRelated: true,
            originalCourseId: null // No hay curso real para este
          }))
        }
      } catch (error) {
        console.warn('Error procesando productos relacionados:', error)
        relatedProducts = []
      }
    }

    // Calcular estadísticas adicionales de las reviews
    const reviewStats = {
      totalReviews: course.reviews?.length || 0,
      averageRating: course.rating_value,
      ratingDistribution: {
        5: course.reviews?.filter((r: any) => r.rating === 5).length || 0,
        4: course.reviews?.filter((r: any) => r.rating === 4).length || 0,
        3: course.reviews?.filter((r: any) => r.rating === 3).length || 0,
        2: course.reviews?.filter((r: any) => r.rating === 2).length || 0,
        1: course.reviews?.filter((r: any) => r.rating === 1).length || 0,
      },
    }

    return NextResponse.json(
      {
        success: true,
        data: {
          ...course,
          reviewStats,
          highlights: highlights || undefined,
          relatedProducts,
        },
      },
      {
        status: 200,
        headers: {
          'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=30',
        },
      }
    )
  } catch (error) {
    console.error('Error fetching course:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Error al obtener curso',
        message: error instanceof Error ? error.message : 'Error desconocido',
      },
      { status: 500 }
    )
  }
}