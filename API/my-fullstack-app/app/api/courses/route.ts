import { NextRequest, NextResponse } from 'next/server'
import connectDB from '@/lib/mongoose'
import Course from '@/lib/models/course'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    await connectDB()

    const { searchParams } = new URL(request.url)
    const search = searchParams.get('search') || ''
    const category = searchParams.get('category')
    const language = searchParams.get('language')
    const minRating = searchParams.get('minRating')
    const minPrice = searchParams.get('minPrice')
    const maxPrice = searchParams.get('maxPrice')
    const sortBy = searchParams.get('sortBy') || 'rating_value'
    const order = searchParams.get('order') || 'desc'
    const limit = parseInt(searchParams.get('limit') || '20')
    const page = parseInt(searchParams.get('page') || '1')
    const skip = (page - 1) * limit

    // Si hay búsqueda de texto, usar Atlas Search con facets
    if (search) {
      // Construir filtros adicionales
      const mustClauses: any[] = []
      
      if (category && category !== 'all') {
        mustClauses.push({
          text: {
            query: category,
            path: 'general_category'
          }
        })
      }
      
      if (language && language !== 'all') {
        mustClauses.push({
          text: {
            query: language,
            path: 'language'
          }
        })
      }
      
      if (minRating) {
        mustClauses.push({
          range: {
            path: 'rating_value',
            gte: parseFloat(minRating)
          }
        })
      }

      if (minPrice || maxPrice) {
        const priceRange: any = { path: 'price' }
        if (minPrice) priceRange.gte = parseFloat(minPrice)
        if (maxPrice) priceRange.lte = parseFloat(maxPrice)
        mustClauses.push({ range: priceRange })
      }

      // 1. Pipeline para obtener metadata con facets
      const metaPipeline = [
        {
          $searchMeta: {
            index: 'default',
            facet: {
              operator: {
                compound: {
                  should: [
                    {
                      text: {
                        query: search,
                        path: ['title', 'description', 'short-description', 'authorComment'],
                        fuzzy: {
                          maxEdits: 2,
                          prefixLength: 3
                        }
                      }
                    }
                  ],
                  must: mustClauses.length > 0 ? mustClauses : undefined
                }
              },
              facets: {
                // Facet: general_category (stringFacet)
                categoryFacet: {
                  type: 'string' as const,
                  path: 'general_category',
                  numBuckets: 50
                },
                // Facet: language (stringFacet)
                languageFacet: {
                  type: 'string' as const,
                  path: 'language',
                  numBuckets: 20
                },
                // Facet: price (numberFacet) - NUEVO: 0-25, 25-50, 50-75, 75-100, 100+
                priceFacet: {
                  type: 'number' as const,
                  path: 'price',
                  boundaries: [0, 25, 50, 75, 100, 10000],
                  default: 'other'
                },
                // Facet: rating_value (numberFacet)
                ratingFacet: {
                  type: 'number' as const,
                  path: 'rating_value',
                  boundaries: [0, 1, 2, 3, 4, 5, 6],
                  default: 'other'
                }
              }
            }
          }
        }
      ]

      // Obtener metadata con facets
      const metadataResult = await Course.aggregate(metaPipeline)
      const searchMeta = metadataResult[0] || {}
      const facetsData = searchMeta.facet || {}
      const totalCount = searchMeta.count?.lowerBound || 0

      console.log('🔍 Rating Facets desde Atlas:', JSON.stringify(facetsData.ratingFacet, null, 2))

      // 2. Pipeline para obtener documentos con highlighting
      const docsPipeline = [
        {
          $search: {
            index: 'default',
            compound: {
              should: [
                {
                  text: {
                    query: search,
                    path: ['title', 'description', 'short-description', 'authorComment'],
                    fuzzy: {
                      maxEdits: 2,
                      prefixLength: 3
                    }
                  }
                }
              ],
              must: mustClauses.length > 0 ? mustClauses : undefined
            },
            highlight: {
              path: ['title', 'description', 'short-description', 'authorComment']
            }
          }
        },
        {
          $addFields: {
            searchScore: { $meta: 'searchScore' },
            highlights: { $meta: 'searchHighlights' }
          }
        },
        {
          $sort: { searchScore: -1, [sortBy]: order === 'asc' ? 1 : -1 }
        },
        { $skip: skip },
        { $limit: limit },
        { $project: { __v: 0 } }
      ]

      const courses = await Course.aggregate(docsPipeline)
      const totalPages = Math.ceil(totalCount / limit)

      // Procesar facets de rating - COMBINAR BUCKETS 4 Y 5
      const ratingBuckets = facetsData.ratingFacet?.buckets || []
      
      // Crear un mapa para combinar los conteos
      const ratingMap = new Map<number, number>()
      
      ratingBuckets
        .filter((b: any) => b._id !== 'other' && typeof b._id === 'number' && b._id < 5)
        .forEach((b: any) => {
          ratingMap.set(b._id, (ratingMap.get(b._id) || 0) + b.count)
        })
      
      // Encontrar y combinar el bucket de 5-6 con el de 4-5
      const bucket5 = ratingBuckets.find((b: any) => b._id === 5)
      if (bucket5) {
        ratingMap.set(4, (ratingMap.get(4) || 0) + bucket5.count)
      }
      
      const ratingDistribution = Array.from(ratingMap.entries())
        .map(([id, count]) => ({ _id: id, count }))
        .sort((a, b) => a._id - b._id)

      console.log('📊 Rating Distribution procesado:', JSON.stringify(ratingDistribution, null, 2))

      // Procesar facets de precio - COMBINAR BUCKET 100-10000 como "100+"
      const priceBuckets = facetsData.priceFacet?.buckets || []
      
      const priceMap = new Map<number, number>()
      
      priceBuckets
        .filter((b: any) => b._id !== 'other' && typeof b._id === 'number' && b._id < 100)
        .forEach((b: any) => {
          priceMap.set(b._id, (priceMap.get(b._id) || 0) + b.count)
        })
      
      // Combinar bucket 100-10000 como bucket 100
      const bucket100 = priceBuckets.find((b: any) => b._id === 100)
      if (bucket100) {
        priceMap.set(100, (priceMap.get(100) || 0) + bucket100.count)
      }
      
      const priceBucketsProcessed = Array.from(priceMap.entries())
        .map(([range, count]) => ({ range, count }))
        .sort((a, b) => a.range - b.range)

      const priceStats = {
        minPrice: 0,
        maxPrice: 0,
        avgPrice: 0,
        buckets: priceBucketsProcessed
      }

      if (priceBucketsProcessed.length > 0) {
        const prices = priceBucketsProcessed.map(b => b.range)
        if (prices.length > 0) {
          priceStats.minPrice = Math.min(...prices)
          priceStats.maxPrice = Math.max(...prices)
        }
      }

      return NextResponse.json({
        success: true,
        data: courses,
        pagination: {
          currentPage: page,
          totalPages,
          totalCount,
          limit,
          hasNextPage: page < totalPages,
          hasPrevPage: page > 1,
        },
        facets: {
          categories: (facetsData.categoryFacet?.buckets || []).map((b: any) => ({
            name: b._id,
            count: b.count
          })),
          languages: (facetsData.languageFacet?.buckets || []).map((b: any) => ({
            name: b._id,
            count: b.count
          })),
          priceRange: priceStats,
          ratingDistribution: ratingDistribution
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
      })

    } else {
      // Sin búsqueda de texto - Usar queries normales
      const matchQuery: any = {}
      
      if (category && category !== 'all') {
        matchQuery.general_category = category
      }
      if (language && language !== 'all') {
        matchQuery.language = language
      }
      if (minRating) {
        matchQuery.rating_value = { $gte: parseFloat(minRating) }
      }
      if (minPrice || maxPrice) {
        matchQuery.price = {}
        if (minPrice) matchQuery.price.$gte = parseFloat(minPrice)
        if (maxPrice) matchQuery.price.$lte = parseFloat(maxPrice)
      }

      const basePipeline: any[] = []
      if (Object.keys(matchQuery).length > 0) {
        basePipeline.push({ $match: matchQuery })
      }

      const pipeline = [
        ...basePipeline,
        {
          $facet: {
            total: [{ $count: 'count' }],
            categories: [
              { $sortByCount: '$general_category' },
              { $limit: 50 }
            ],
            languages: [
              { $sortByCount: '$language' },
              { $limit: 20 }
            ],
            priceStats: [
              {
                $group: {
                  _id: null,
                  minPrice: { $min: '$price' },
                  maxPrice: { $max: '$price' },
                  avgPrice: { $avg: '$price' }
                }
              }
            ],
            priceDistribution: [
              {
                $bucket: {
                  groupBy: '$price',
                  boundaries: [0, 25, 50, 75, 100, 10000],
                  default: 'other',
                  output: {
                    count: { $sum: 1 }
                  }
                }
              }
            ],
            ratingDistribution: [
              {
                $bucket: {
                  groupBy: '$rating_value',
                  boundaries: [0, 1, 2, 3, 4, 5, 6],
                  default: 'Other',
                  output: { count: { $sum: 1 } }
                }
              }
            ],
            results: [
              { $sort: { [sortBy]: order === 'asc' ? 1 : -1 } },
              { $skip: skip },
              { $limit: limit },
              { $project: { __v: 0 } }
            ]
          }
        }
      ]

      const aggregationResult = await Course.aggregate(pipeline)
      const data = aggregationResult[0]
      
      const totalCount = data.total[0]?.count || 0
      const courses = data.results
      const totalPages = Math.ceil(totalCount / limit)

      console.log('📊 Rating Distribution (sin búsqueda):', JSON.stringify(data.ratingDistribution, null, 2))

      // Procesar ratings para combinar bucket 5 con bucket 4
      const ratingMapNormal = new Map<number, number>()
      
      data.ratingDistribution
        .filter((b: any) => b._id !== 'Other' && typeof b._id === 'number' && b._id < 5)
        .forEach((b: any) => {
          ratingMapNormal.set(b._id, (ratingMapNormal.get(b._id) || 0) + b.count)
        })
      
      // Combinar bucket 5 con bucket 4
      const bucket5Normal = data.ratingDistribution.find((b: any) => b._id === 5)
      if (bucket5Normal) {
        ratingMapNormal.set(4, (ratingMapNormal.get(4) || 0) + bucket5Normal.count)
      }
      
      const processedRatingDistribution = Array.from(ratingMapNormal.entries())
        .map(([id, count]) => ({ _id: id, count }))
        .sort((a, b) => a._id - b._id)

      // Procesar precios para combinar bucket 100-10000 como "100+"
      const priceMapNormal = new Map<number, number>()
      
      data.priceDistribution
        .filter((b: any) => b._id !== 'other' && typeof b._id === 'number' && b._id < 100)
        .forEach((b: any) => {
          priceMapNormal.set(b._id, (priceMapNormal.get(b._id) || 0) + b.count)
        })
      
      // Combinar bucket 100-10000 como bucket 100
      const bucket100Normal = data.priceDistribution.find((b: any) => b._id === 100)
      if (bucket100Normal) {
        priceMapNormal.set(100, (priceMapNormal.get(100) || 0) + bucket100Normal.count)
      }
      
      const processedPriceDistribution = Array.from(priceMapNormal.entries())
        .map(([range, count]) => ({ range, count }))
        .sort((a, b) => a.range - b.range)

      return NextResponse.json({
        success: true,
        data: courses,
        pagination: {
          currentPage: page,
          totalPages,
          totalCount,
          limit,
          hasNextPage: page < totalPages,
          hasPrevPage: page > 1,
        },
        facets: {
          categories: data.categories.map((c: any) => ({
            name: c._id,
            count: c.count
          })),
          languages: data.languages.map((l: any) => ({
            name: l._id,
            count: l.count
          })),
          priceRange: {
            ...(data.priceStats[0] || { minPrice: 0, maxPrice: 0, avgPrice: 0 }),
            buckets: processedPriceDistribution
          },
          ratingDistribution: processedRatingDistribution
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
      })
    }
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