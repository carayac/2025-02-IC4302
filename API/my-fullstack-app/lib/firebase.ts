import { initializeApp } from "firebase/app"
import { getAuth } from "firebase/auth"
import { getFirestore } from "firebase/firestore" 

// Configuración de credenciales de Firebase
const firebaseConfig = {
  apiKey: "apikey",
  authDomain: "authdomain",
  projectId: "projectId",
  storageBucket: "storageBucket",
  messagingSenderId: "messagingSenderId",
  appId: "appId",
  measurementId: "G-measurementId",
}

// Se inicializa la app de Firebase para usar servicios de autenticación y de la base de datos
const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const db = getFirestore(app)
