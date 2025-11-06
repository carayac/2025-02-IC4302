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

    // Buscar curso por ID
    const course = await Course.findById(id)
      .select('-__v') // Excluir campo __v
      .lean() // Retornar objeto plano

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
      totalReviews: course.reviews.length,
      averageRating: course.rating_value,
      ratingDistribution: {
        5: course.reviews.filter((r) => r.rating === 5).length,
        4: course.reviews.filter((r) => r.rating === 4).length,
        3: course.reviews.filter((r) => r.rating === 3).length,
        2: course.reviews.filter((r) => r.rating === 2).length,
        1: course.reviews.filter((r) => r.rating === 1).length,
      },
    }

    return NextResponse.json(
      {
        success: true,
        data: {
          ...course,
          reviewStats,
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
    console.error('❌ Error fetching course:', error)
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