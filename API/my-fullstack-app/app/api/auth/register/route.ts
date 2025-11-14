import { NextRequest, NextResponse } from 'next/server'
import { authAdmin } from '@/lib/firebase-admin'
import { db } from '@/lib/firebase'
import { doc, setDoc } from 'firebase/firestore'

export async function POST(request: NextRequest) {

    // Obtiene los datos del cuerpo de la solicitud
    const { email, password } = await request.json()
    try {
        // Crea el usuario con la funcionalidad de Firebase Authentication
        const userRecord = await authAdmin.createUser({ email, password })
        await setDoc(doc(db, 'users', userRecord.uid), {
        email,
        createdAt: new Date(),
        })
        // Respuesta exitosa con UID del usuario
        return NextResponse.json({ success: true, uid: userRecord.uid })
    } catch (error) {
        return NextResponse.json({ success: false, error: (error as Error).message }, { status: 400 })
    }
    }