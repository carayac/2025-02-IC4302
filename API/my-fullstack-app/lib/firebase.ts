import { initializeApp } from "firebase/app"
import { getAuth } from "firebase/auth"

// Configuración de credenciales de Firebase
const firebaseConfig = {
  apiKey: "AIzaSyBGqepgUpRN9jfTfRnzSMiFOnXEEzSJ8VU",
  authDomain: "proyect-db-2-itcr.firebaseapp.com",
  projectId: "proyect-db-2-itcr",
  storageBucket: "proyect-db-2-itcr.firebasestorage.app",
  messagingSenderId: "121361936291",
  appId: "1:121361936291:web:c0d99e83a723641fa3b416",
  measurementId: "G-DZ3Q95442D",
}

// Se inicializa la app de Firebase para usar servicios de autenticación
const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)