import { LoginForm } from "@/components/auth/login-form"

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-background via-background to-background/80 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight"> Products Search V2 </h1>
          <p className="mt-2 text-muted-foreground">Gestiona tu cuenta de forma segura</p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}