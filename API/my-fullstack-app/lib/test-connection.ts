import dotenv from 'dotenv'
import { resolve } from 'path'

// Cargar variables de entorno ANTES de cualquier otro import
dotenv.config({ path: resolve(__dirname, '../.env.local') })

// Ahora sí importar connectDB después de cargar las variables
async function testConnection() {
  try {
    console.log('🔄 Intentando conectar a MongoDB...')
    console.log('📍 MONGODB_URI:', process.env.MONGODB_URI ? '✅ Cargada' : '❌ No encontrada')
    
    // Import dinámico después de cargar env
    const { default: connectDB } = await import('./mongoose')
    
    await connectDB()
    console.log('Conexión exitosa a MongoDB')
    process.exit(0)
  } catch (error) {
    console.error('Error en la conexión:', error)
    process.exit(1)
  }
}

testConnection()