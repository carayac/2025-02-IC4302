import { NextRequest, NextResponse } from 'next/server'
import { authAdmin } from '@/lib/firebase-admin' 
import { db } from '@/lib/firebase'  
import { doc, getDoc } from 'firebase/firestore'  

export async function POST(request: NextRequest) {
  // Extrae el token ID del cuerpo de la solicitud JSON
    const { token } = await request.json()
    try {
        // Verifica el token con Firebase Admin (confirma validez y decodifica info del usuario)
        const decodedToken = await authAdmin.verifyIdToken(token)
        
        // Verificación si el usuario existe en Firestore
        const userDoc = await getDoc(doc(db, 'users', decodedToken.uid))
        if (!userDoc.exists()) throw new Error('Usuario no encontrado')
        
        // Respuesta exitosa con UID del usuario
        const response = NextResponse.json({ success: true, uid: decodedToken.uid })
        
        // Setea cookie 'auth-token' con el token verificado con 1 hora de duracion 
        response.cookies.set('auth-token', token, { path: '/', maxAge: 3600 })
        
        return response
    } catch (error) 
        return NextResponse.json({ success: false, error: (error as Error).message }, { status: 401 })
    }
}