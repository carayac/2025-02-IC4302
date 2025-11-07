import { NextRequest, NextResponse } from 'next/server'
import connectDB from '@/lib/mongoose'
import Course from '@/lib/models/course'
import mongoose from 'mongoose'

export const dynamic = 'force-dynamic'

/**
 * GET /api/courses/[id]
 * Obtiene un curso específico por ID
 */
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