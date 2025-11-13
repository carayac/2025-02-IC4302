export const runtime = 'nodejs'
// Importa NextResponse para crear respuestas HTTP y NextRequest para tipar la solicitud
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Importa authAdmin desde firebase-admin para verificar tokens
import { authAdmin } from '@/lib/firebase-admin'

// Función middleware que recibe la solicitud
export async function middleware(request: NextRequest) {
  // Obtiene el token de la cookie 'auth-token' (si existe)
  const token = request.cookies.get('auth-token')?.value

  // Si no hay token y la ruta es '/', redirige a login
  if (!token && request.nextUrl.pathname === '/') {
    return NextResponse.redirect(new URL('/auth/login', request.url))
  }

  // Si hay token, intenta verificarlo con Firebase Admin
  if (token) {
    try {
      // Verifica si el token es válido (no expirado, no revocado)
      await authAdmin.verifyIdToken(token)
    } catch (error) {
      // Si el token es invalido, redirige a login y elimina la cookie
      const response = NextResponse.redirect(new URL('/auth/login', request.url))
      response.cookies.set('auth-token', '', { maxAge: 0, path: '/' }) // Borra cookie
      return response
    }
  }

  // Si todo está bien, continúa con la solicitud normal
  return NextResponse.next()
}

// Configura qué rutas aplica el middleware 
export const config = {
  matcher: ['/', '/courses/:path*'],
}