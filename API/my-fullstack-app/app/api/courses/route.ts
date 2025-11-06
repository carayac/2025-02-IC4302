import { NextRequest, NextResponse } from 'next/server'
import connectDB from '@/lib/mongoose'
import Course from '@/lib/models/course'

// Desactivar cache estático para datos dinámicos
export const dynamic = 'force-dynamic'


export async function GET(request: NextRequest) {
  try {
    // Conectar a la base de datos
    await connectDB()

    // Obtener parámetros de búsqueda
    const { searchParams } = new URL(request.url)
    const search = searchParams.get('search')
    const category = searchParams.get('category')
    const language = searchParams.get('language')
    const minRating = searchParams.get('minRating')
    const minPrice = searchParams.get('minPrice')
    const maxPrice = searchParams.get('maxPrice')
    const sortBy = searchParams.get('sortBy') || 'rating_value'
    const order = searchParams.get('order') || 'desc'
    const limit = parseInt(searchParams.get('limit') || '20')
    const page = parseInt(searchParams.get('page') || '1')

    // Construir query dinámico
    const query: any = {}

    // Búsqueda por texto en múltiples campos
    if (search) {
      query.$or = [
        { title: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
        { 'short-description': { $regex: search, $options: 'i' } },
        { general_category: { $regex: search, $options: 'i' } },
      ]
    }

    // Filtrar por categoría
    if (category && category !== 'all') {
      query.general_category = category
    }

    // Filtrar por idioma
    if (language && language !== 'all') {
      query.language = language
    }

    // Filtrar por rating mínimo
    if (minRating) {
      query.rating_value = { $gte: parseFloat(minRating) }
    }

    // Filtrar por rango de precio
    if (minPrice || maxPrice) {
      query.price = {}
      if (minPrice) query.price.$gte = parseFloat(minPrice)
      if (maxPrice) query.price.$lte = parseFloat(maxPrice)
    }

    // Construir ordenamiento
    const sortOrder = order === 'asc' ? 1 : -1
    const sortOptions: any = { [sortBy]: sortOrder }

    // Calcular skip para paginación
    const skip = (page - 1) * limit

    // Ejecutar query con paginación
    const [courses, totalCount] = await Promise.all([
      Course.find(query)
        .select('-__v') // Excluir campo __v de mongoose
        .sort(sortOptions)
        .skip(skip)
        .limit(limit)
        .lean(), // Optimizar performance, retorna objetos planos
      Course.countDocuments(query), // Contar total para paginación
    ])

    // Calcular metadata de paginación
    const totalPages = Math.ceil(totalCount / limit)
    const hasNextPage = page < totalPages
    const hasPrevPage = page > 1

    return NextResponse.json(
      {
        success: true,
        data: courses,
        pagination: {
          currentPage: page,
          totalPages,
          totalCount,
          limit,
          hasNextPage,
          hasPrevPage,
        },
        filters: {
          search,
          category,
          language,
          minRating,
          minPrice,
          maxPrice,
          sortBy,
          order,
        },
      },
      {
        status: 200,
        headers: {
          'Cache-Control': 'no-store, max-age=0', // No cachear datos dinámicos
        },
      }
    )
  } catch (error) {
    console.error('Error fetching courses:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Error al obtener cursos',
        message: error instanceof Error ? error.message : 'Error desconocido',
      },
      { status: 500 }
    )
  }
}